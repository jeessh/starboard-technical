# Technical Interview: Email Extraction Agent

## The Problem

Freight forwarders receive hundreds of quote request emails daily. Each email contains shipment details buried in unstructured text - origins, destinations, cargo specs, and service requirements. Manually extracting this information is tedious and error-prone.

Your task: **Build an LLM-based agent that extracts structured shipment data from these emails.**

## What You're Given

- `input-emails/` - 7 sample quote request emails (varying complexity)
- `schema.json` - The expected output format
- `example-outputs/` - One example output to show expected format
- An OpenAI API key (provided separately)

## What We're Looking For

1. **A working extraction system** - Can your agent accurately pull the right data?
2. **Handling ambiguity** - Some emails have missing info, multiple shipments, or unclear wording
3. **Clean, readable code** - We'll review your implementation approach
4. **Your reasoning** - Brief notes on assumptions and design decisions
5. **Cost efficiency** - Track and report your total API token usage (input + output tokens) for processing all 7 emails. Our production system handles thousands of emails daily, so cost matters.

You don't need freight industry expertise. If terminology is unclear, ask the interviewer.

## Time Limit

2 Hours

## Deliverables

1. Your source code
2. Output JSON files for each input email (matching input filenames, e.g., `01_yantian_to_chicago_fcl.json`)
3. Brief notes (<1 page) explaining your approach and any assumptions
4. Token usage report (total input/output tokens used across all 7 emails)

## Key Requirements

- Output must be valid JSON matching `schema.json`
- Use `null` for fields not present in the email
- One email may contain **multiple shipment requests** - capture all of them
- Convert weights to **kg** and volumes to **CBM**

## Example Output

Check `example-outputs/` for one worked example. Use it to understand:
- The expected JSON structure
- How to handle missing fields (use `null`)
- The level of detail expected

---

## Schema Quick Reference

Your output should match this structure:

```json
{
  "sender": {
    "name": "string",
    "email": "string",
    "company": "string | null",
    "phone": "string | null"
  },
  "shipments": [
    {
      "origin": {
        "city": "string",
        "country": "string",
        "address": "string | null"
      },
      "destination": {
        "city": "string",
        "country": "string",
        "address": "string | null"
      },
      "cargo": {
        "description": "string | null",
        "weight_kg": "number | null",
        "volume_cbm": "number | null",
        "container_type": "string | null",
        "container_count": "number | null",
        "piece_count": "number | null"
      },
      "transport_mode": "ocean_fcl | ocean_lcl | air | null",
      "incoterm": "string | null",
      "special_requirements": ["string"]
    }
  ]
}
```

**Key points:**
- `transport_mode` must be one of: `ocean_fcl`, `ocean_lcl`, `air`, or `null`
- One email requesting quotes for multiple routes = multiple shipment objects
- One email requesting quotes for different modes (e.g., Air AND LCL) = multiple shipment objects
- Convert weights to kg and volumes to CBM
- Use `null` for fields not specified in the email

---

## Questions?

Feel free to ask clarifying questions about the task or domain terminology.
