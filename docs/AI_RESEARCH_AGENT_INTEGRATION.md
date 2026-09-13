# AI Research Agent Integration Contract

The research Agent owns question decomposition, memo composition, and final
communication. FinEvidence owns evidence retrieval, provenance, citation
resolution, and the evidence qualification gate. The Agent must not silently
replace an `INSUFFICIENT` result with model-generated confidence.

## Recommended call sequence

```text
question
  -> POST /api/v1/evidence/search
  -> build or load typed requirements
  -> POST /api/v1/evidence/coverage
  -> if PARTIAL/INSUFFICIENT, retrieve again with missing requirement context
  -> require ELIGIBLE before grounded answer generation
  -> resolve each cited ID with GET /api/v1/evidence/{id}/citation
```

Minimal search call:

```powershell
$body = @{ query = "HSBC CET1 ratio 2025"; top_k = 5 } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/v1/evidence/search -Method Post -ContentType application/json -Body $body
```

The Agent should pass evidence IDs, not copied text, into the coverage request
so the service can preserve identity and independently evaluate support. It
should expose page/document citations returned by the service and should not
claim region-level grounding when `bbox` is null.

`/api/v1/table/query` is useful for exact entity/metric/period lookup. It does
not execute arbitrary SQL and does not invent missing table facts. `/verify`
is a single-claim convenience wrapper over the same qualification semantics.

This document deliberately does not define an Agent loop, tool planner,
memory system, or generation prompt. Those remain outside the Evidence
Backend boundary.
