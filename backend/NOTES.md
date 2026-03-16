# Approach & Assumptions

## Design Decisions

### Model Choice: `gpt-4o-mini`
Chosen for its strong balance of extraction accuracy and cost. At ~1/20th the price
of GPT-4o, it handles structured extraction tasks well when given a precise system
prompt. Emails are short (< 500 tokens each), so context length is not a concern.

### JSON Mode
All API calls use `response_format={"type": "json_object"}`. This guarantees the
model always returns parseable JSON and reduces prompt-following failures.
`temperature=0` makes results deterministic.

### Single-Pass, No Tool Calls
Each email is processed in a single LLM call. The schema is embedded directly in
the system prompt so the model has full context. A retry wrapper catches any
validation failures. No multi-step agent loop is needed for this extraction task –
it would only add latency and cost.

### Schema Embedded in System Prompt
Including the full `schema.json` (with descriptions) in the system prompt gives
the model precise field-level guidance (e.g., the distinction between
`ocean_fcl` vs `ocean_lcl`, that `address` is only for door-to-door). This
reduces hallucinations and improves null-handling.

### Validation
Every response is validated against `schema.json` via `jsonschema` before being
written to disk. A failed validation raises an error with the specific violation.

---

## Key Extraction Rules in the Prompt

| Scenario | Handling |
|---|---|
| Multiple routes in one email | Separate `shipments[]` entry per route |
| Multiple transport modes (e.g. Air + LCL) | Separate `shipments[]` entry per mode |
| Weight in lbs | Converted to kg (× 0.453592) |
| Weight in metric tons | Converted to kg (× 1000) |
| Door pickup/delivery address | Placed in `origin.address` / `destination.address` |
| Missing field | `null` |
| Special requirements | Captured in `special_requirements[]` array |

---

## Assumptions

- **Email 02 (table format)**: "Collect" shipping terms are not a standard incoterm;
  mapped to `null` for `incoterm`. The delivery address (CT) is treated as
  `destination.address`, while the port quote is NY → Nhava Sheva, so
  `destination.city = "New York"`. No explicit FCL/LCL distinction beyond "40'
  container" → `ocean_fcl`.
- **Email 03 (multi-lane)**: Two separate routes (Shakopee MN and Mississauga ON)
  sharing the same cargo spec → two shipment objects.
- **Email 05 (multi-origin)**: Two pickup addresses (Houston and Atlanta) shipping
  to the same Indian destination → two shipment objects (one per origin).
- **Email 06 (Air + LCL)**: One cargo, two requested modes → two shipment objects
  with the same origin/destination/cargo but different `transport_mode`.
- **Email 07 (reefer)**: `40RFHC` (40ft Reefer High Cube) treated as container
  type `"40HC"` with temperature requirement captured in `special_requirements`.
  No weight/volume given → `null`.

---

## Cost Efficiency Notes

- `gpt-4o-mini` pricing (as of early 2026): ~$0.15/1M input tokens, ~$0.60/1M output
  tokens — approximately 20× cheaper than `gpt-4o`.
- All 7 emails combined are short; total expected token cost is well under $0.01.
- In production, the system prompt (schema) could be cached with OpenAI's prompt
  caching feature to further reduce repeated input token costs across thousands of
  daily emails.
