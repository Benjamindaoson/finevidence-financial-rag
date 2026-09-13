# FinEvidence Evidence Backend v1

## Release boundary

This release turns the existing evidence-first research primitives into a
small, callable backend. It does not change historical P0–B4 experiment
results and does not claim production deployment readiness.

## Included

- versioned, provenance-bearing `EvidenceObject`;
- deterministic search over the configured local evidence catalog;
- requirement-aware independent coverage and single-claim verification;
- metadata-first table evidence query;
- citation lookup with document hash, page, table identity, and optional bbox;
- fail-closed boundary for unsupported security filters;
- FastAPI contract tests, Docker packaging, and Agent integration guidance.

## Start locally

```powershell
cd "D:\01_work\Enterprise Multimodal RAG\finevidence"
.\.venv\Scripts\python.exe -m uvicorn finevidence.api.app:app --host 127.0.0.1 --port 8000
```

Then check `http://127.0.0.1:8000/health` or the OpenAPI document at
`http://127.0.0.1:8000/docs`.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src tests scripts
```

See [FIN_EVIDENCE_ARCHITECTURE.md](FIN_EVIDENCE_ARCHITECTURE.md),
[FIN_EVIDENCE_API_SPEC.md](FIN_EVIDENCE_API_SPEC.md), and
[AI_RESEARCH_AGENT_INTEGRATION.md](AI_RESEARCH_AGENT_INTEGRATION.md).
