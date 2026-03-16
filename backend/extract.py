"""
Freight RFQ Email Extraction Agent
-----------------------------------
Reads plain-text freight quote request emails and extracts structured JSON
matching candidate-package/schema.json using the OpenAI API.

Usage:
    export OPENAI_API_KEY="sk-..."
    python extract.py

Outputs:
    - JSON files written to candidate-package/example-outputs/
    - Token usage summary printed to stdout
"""

import json
import os
import sys
from pathlib import Path
from openai import OpenAI
import jsonschema
from dotenv import load_dotenv

# Load .env if it exists
load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent / "candidate-package"
EMAILS_DIR = BASE_DIR / "input-emails"
OUTPUT_DIR = BASE_DIR / "example-outputs"
SCHEMA_PATH = BASE_DIR / "schema.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Model config – gpt-4o-mini balances cost and accuracy well for extraction
# ---------------------------------------------------------------------------
MODEL = "gpt-4o-mini"

# ---------------------------------------------------------------------------
# Pre-classification + normalization prompts
# ---------------------------------------------------------------------------
CLASSIFICATION_PROMPT = """You are classifying freight quote request emails.

Determine whether the input should be treated as a RATE SHEET style request.

Classify as is_rate_sheet=true when the email is primarily structured like any of:
- a table
- field/value pairs
- spreadsheet-like rows
- checklist/form layout
- dense spec sheet with labeled attributes

Classify as is_rate_sheet=false when the email is primarily normal prose / free text,
even if it contains a few labeled lines like POL/POD.

Return JSON only in this exact shape:
{
    "is_rate_sheet": true,
    "reason": "brief explanation"
}
"""

RATE_SHEET_NORMALIZATION_PROMPT = """You are rewriting freight quote rate-sheet emails
into a deterministic canonical text format for a downstream extractor.

Your task:
1. Read the raw rate sheet / table / field-value email.
2. Convert it into clean plain text sections.
3. Preserve all factual details exactly.
4. Do NOT infer missing values.
5. Do NOT convert units.
6. Keep one fact per line where practical.

Output JSON only in this exact shape:
{
    "normalized_email": "..."
}

Use a format like:
Subject: ...
From: ...

Sender:
- Name: ...
- Company: ...
- Phone: ...
- Email: ...

Shipment Request:
- Origin city: ...
- Origin country: ...
- Destination city: ...
- Destination country: ...
- Destination address: ...
- Mode requested: ...
- Container: ...
- Container count: ...
- Cargo description: ...
- Weight: ...
- Volume: ...
- Piece count: ...
- Incoterm / shipping terms: ...
- Special requirements: ...

Include any additional factual rows under the most relevant heading.
"""

EXTRACTION_PROMPT = """You are a freight logistics data extraction specialist.

Your job is to read a raw freight quote request (RFQ) email and extract all
shipment information into a structured JSON object. The output will be post-processed
for unit conversion, so focus on accurate data extraction and labeling.

OUTPUT RULES:
1. Return ONLY valid JSON – no markdown, no code fences, no extra text.
2. Use null for any field not mentioned in the email.
3. special_requirements must be an array (empty [] if none).
4. transport_mode must be exactly one of: "ocean_fcl", "ocean_lcl", "air", or null.
   - FCL / full container load → "ocean_fcl"
   - LCL / less than container load → "ocean_lcl"
   - Air / airfreight → "air"
5. If an email requests quotes for MULTIPLE transport modes (e.g. both Air AND LCL),
   create a SEPARATE shipment object for each mode.
6. If an email requests quotes for MULTIPLE routes/lanes, create a SEPARATE
   shipment object for each route.
7. WEIGHT/VOLUME EXTRACTION (DO NOT CONVERT):
   - Extract weight as a single number and indicate the detected unit:
     * If you see "lbs" or "lb" → use "weight_lbs" field
     * If you see "kg" → use "weight_kg" field
     * If you see "metric tons" or "MT" → use "weight_metric_tons" field
   - Extract volume as a single number and indicate the detected unit:
     * If you see "cbm", "m³", or "CBM" → use "volume_cbm" field
   - Python will convert all to target units (always kg and CBM).
8. Container sizes: normalise to "20ft", "40ft", or "40HC" where clear.
9. Capture door pickup/delivery addresses in origin.address / destination.address.
10. incoterm: extract as-is (e.g. "FOB", "DDP", "EXW", "CIF"). Use null if absent.
11. special_requirements: include things like temperature requirements, free time,
    reefer/DG/hazmat flags, itemised cost requests, stackability notes, etc.

SCHEMA (final output structure – Python will post-process unit fields):
{schema}
"""

# ---------------------------------------------------------------------------
# Load schema once
# ---------------------------------------------------------------------------
with open(SCHEMA_PATH, "r") as f:
    SCHEMA = json.load(f)

FILLED_EXTRACTION_PROMPT = EXTRACTION_PROMPT.format(schema=json.dumps(SCHEMA, indent=2))


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------
def _json_completion(client: OpenAI, system_prompt: str, user_prompt: str) -> tuple[dict, dict]:
    """Run a JSON-mode completion and return (parsed_json, usage)."""
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )

    raw_json = response.choices[0].message.content
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {exc}\n{raw_json}")

    usage = {
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    return parsed, usage


def classify_email_format(client: OpenAI, email_text: str) -> tuple[bool, dict, dict]:
    """Classify whether an email is rate-sheet-like."""
    parsed, usage = _json_completion(
        client,
        CLASSIFICATION_PROMPT,
        f"Classify this freight email:\n\n{email_text}",
    )

    if "is_rate_sheet" not in parsed:
        raise ValueError("Classification response missing 'is_rate_sheet'")

    return bool(parsed["is_rate_sheet"]), parsed, usage


def normalize_rate_sheet(client: OpenAI, email_text: str) -> tuple[str, dict]:
    """Rewrite a rate-sheet email into canonical plain text for extraction."""
    parsed, usage = _json_completion(
        client,
        RATE_SHEET_NORMALIZATION_PROMPT,
        f"Normalize this freight rate-sheet email:\n\n{email_text}",
    )

    normalized = parsed.get("normalized_email")
    if not isinstance(normalized, str) or not normalized.strip():
        raise ValueError("Normalization response missing 'normalized_email'")

    return normalized, usage


# ---------------------------------------------------------------------------
# Unit conversion post-processor
# ---------------------------------------------------------------------------
def convert_units(data: dict) -> dict:
    """
    Post-process extracted data to convert weights and volumes to schema units.
    The LLM extracts with unit indicators (weight_lbs, weight_kg, volume_cbm, etc.),
    and this function converts all to target units: kg and CBM.
    """
    for shipment in data.get("shipments", []):
        cargo = shipment.get("cargo", {})

        # Handle weight conversion to kg
        weight_kg = None
        if "weight_lbs" in cargo and cargo["weight_lbs"] is not None:
            weight_kg = round(cargo["weight_lbs"] * 0.453592, 4)
            del cargo["weight_lbs"]
        elif "weight_metric_tons" in cargo and cargo["weight_metric_tons"] is not None:
            weight_kg = round(cargo["weight_metric_tons"] * 1000, 4)
            del cargo["weight_metric_tons"]
        elif "weight_kg" in cargo and cargo["weight_kg"] is not None:
            weight_kg = cargo["weight_kg"]

        cargo["weight_kg"] = weight_kg

        # Handle volume conversion to CBM
        volume_cbm = None
        if "volume_m3" in cargo and cargo["volume_m3"] is not None:
            volume_cbm = cargo["volume_m3"]  # 1 m³ = 1 CBM
            del cargo["volume_m3"]
        elif "volume_cbm" in cargo and cargo["volume_cbm"] is not None:
            volume_cbm = cargo["volume_cbm"]

        cargo["volume_cbm"] = volume_cbm

    return data


# ---------------------------------------------------------------------------
# Extraction function
# ---------------------------------------------------------------------------
def extract_rfq(client: OpenAI, email_text: str, filename: str) -> tuple[dict, dict]:
    """
    Send one email to the LLM and return (parsed_result, usage_dict).
    Raises ValueError if the response is not valid JSON or fails schema validation.
    """
    total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    # Stage 1: classify input shape
    is_rate_sheet, _classification, usage = classify_email_format(client, email_text)
    for key in total_usage:
        total_usage[key] += usage[key]

    # Stage 2: if needed, normalize rate-sheet/table content into canonical text
    extraction_input = email_text
    if is_rate_sheet:
        extraction_input, usage = normalize_rate_sheet(client, email_text)
        for key in total_usage:
            total_usage[key] += usage[key]

    # Stage 3: run the original extraction logic against the chosen input
    try:
        result, usage = _json_completion(
            client,
            FILLED_EXTRACTION_PROMPT,
            f"Extract the shipment data from this email:\n\n{extraction_input}",
        )
    except ValueError as exc:
        raise ValueError(f"[{filename}] {exc}")

    for key in total_usage:
        total_usage[key] += usage[key]

    # Post-process units (convert to kg, CBM)
    result = convert_units(result)

    # Validate against schema
    try:
        jsonschema.validate(instance=result, schema=SCHEMA)
    except jsonschema.ValidationError as exc:
        raise ValueError(f"[{filename}] Schema validation failed: {exc.message}")

    return result, total_usage


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # Load .env file, overriding any existing environment variables
    load_dotenv(override=True)
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Error: OPENAI_API_KEY environment variable not set.")

    client = OpenAI(api_key=api_key)

    email_files = sorted(EMAILS_DIR.glob("*.txt"))
    if not email_files:
        sys.exit(f"No .txt files found in {EMAILS_DIR}")

    total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    results_summary = []

    print(f"Processing {len(email_files)} email(s) with model={MODEL}\n")
    print("-" * 60)

    for email_path in email_files:
        stem = email_path.stem  # e.g. "01_yantian_to_chicago_fcl"
        output_path = OUTPUT_DIR / f"{stem}.json"

        email_text = email_path.read_text(encoding="utf-8")

        try:
            result, usage = extract_rfq(client, email_text, email_path.name)

            # Write output
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            shipment_count = len(result.get("shipments", []))
            status = f"OK  ({shipment_count} shipment{'s' if shipment_count != 1 else ''})"
        except (ValueError, Exception) as exc:
            status = f"FAILED – {exc}"
            usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        # Accumulate totals
        for k in total_usage:
            total_usage[k] += usage[k]

        results_summary.append(
            {
                "file": email_path.name,
                "status": status,
                "output": str(output_path) if "OK" in status else None,
                **usage,
            }
        )

        print(
            f"  {email_path.name:<45} {status:<30} "
            f"in={usage['input_tokens']:>5}  out={usage['output_tokens']:>4}"
        )

    # ---------------------------------------------------------------------------
    # Token usage report
    # ---------------------------------------------------------------------------
    print("-" * 60)
    print("\nToken Usage Report")
    print("=" * 60)
    print(f"  {'File':<45} {'Input':>7}  {'Output':>7}  {'Total':>7}")
    print(f"  {'-'*45}  {'-'*7}  {'-'*7}  {'-'*7}")
    for r in results_summary:
        print(
            f"  {r['file']:<45} {r['input_tokens']:>7}  {r['output_tokens']:>7}  {r['total_tokens']:>7}"
        )
    print(f"  {'-'*45}  {'-'*7}  {'-'*7}  {'-'*7}")
    print(
        f"  {'TOTAL':<45} {total_usage['input_tokens']:>7}  "
        f"{total_usage['output_tokens']:>7}  {total_usage['total_tokens']:>7}"
    )
    print("=" * 60)
    print(f"\nOutputs written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
