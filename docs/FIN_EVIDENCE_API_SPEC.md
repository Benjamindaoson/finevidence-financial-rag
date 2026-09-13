# FinEvidence Evidence Backend v1 API

FinEvidence exposes a small HTTP boundary around the existing Evidence IR,
retrieval, alignment, and independent-coverage primitives. The API is an
evidence service, not an answer-generation service.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Process and catalog health |
| POST | `/api/v1/evidence/search` | Search provenance-bearing evidence |
| POST | `/api/v1/evidence/coverage` | Evaluate supplied requirements against evidence |
| POST | `/api/v1/table/query` | Exact metadata-first table evidence query |
| POST | `/api/v1/evidence/verify` | Verify one claim through the coverage gate |
| GET | `/api/v1/evidence/{evidence_id}/citation` | Resolve citation metadata |

## Search

```json
{
  "query": "HSBC CET1 ratio 2025",
  "filters": {"entity": "HSBC", "metric": "CET1 ratio", "period": "2025"},
  "top_k": 10
}
```

The response contains `EvidenceObject` records. Each record keeps identity,
source URL, document hash when available, page, text/table/visual content,
financial slots, table identity, optional geometry, and a verification status.

## Coverage

Coverage accepts explicit serialized `Requirement` records and optional
evidence IDs. A caller should require `status == "ELIGIBLE"` before treating
the evidence set as sufficient for a high-stakes memo. `PARTIAL` and
`INSUFFICIENT` responses preserve missing critical requirement IDs.

```json
{
  "question": "What was HSBC CET1 ratio in 2025?",
  "required_claims": [{
    "requirement_id": "r-current",
    "description": "HSBC CET1 ratio 2025",
    "fact_type": "RETRIEVED_FACT",
    "role": "value",
    "entity": "HSBC",
    "metric": "CET1 ratio",
    "period": "2025",
    "criticality": "CRITICAL",
    "acceptable_evidence_ids": ["doc-1:p3:cell-1"],
    "evidence_role": "VALUE_SUPPORT"
  }],
  "evidence_ids": ["doc-1:p3:cell-1"]
}
```

## Security boundary

`tenant_id` and `user_role` are accepted as security-filter fields so an
upstream authorization adapter has a stable boundary. If no authorizer is
configured, any request containing these fields fails closed with HTTP 403;
the local service never returns unfiltered evidence while implying ACL
enforcement.

## Status codes

- `200`: valid request and service result, including an empty catalog result.
- `403`: requested security filter cannot be authorized by the configured service.
- `404`: citation requested for an unknown evidence ID.
- `422`: malformed JSON or request schema.

## Local run

```powershell
.\.venv\Scripts\python.exe -m uvicorn finevidence.api.app:app --host 127.0.0.1 --port 8000
```

The default process loads the local HSBC page evidence only when the ignored
HSBC artifacts are present; otherwise it starts with an honest empty catalog.
