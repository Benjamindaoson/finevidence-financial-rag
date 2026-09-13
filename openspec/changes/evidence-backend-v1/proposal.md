# Evidence Backend v1

## Why

The repository has reusable evidence retrieval and qualification primitives, but no stable boundary for a future AI Investment Research Agent. Directly exposing experiment runners would couple the Agent to benchmark internals and make provenance/verification optional.

## Scope

Add a thin FastAPI service and versioned `EvidenceObject` contract for evidence search, coverage, table lookup, verification, and citation lookup. Reuse existing retrievers and qualification functions. Keep the service local/development-oriented and preserve all prior experiments, datasets, reports, and artifacts.

## Out of scope

No Agent loop, UI, Kubernetes, Redis, distributed serving, new retrieval benchmark, or full ACL/ABAC product is introduced. Security filtering is an explicit adapter boundary and fails closed when unsupported filters are requested.

## Acceptance

- API schemas are stable, strict, and serializable.
- Search returns provenance-bearing EvidenceObjects.
- Coverage and verification reuse existing alignment/coverage semantics.
- Table and citation endpoints expose only indexed, traceable evidence.
- `/health` is available for local service checks.
- Contract tests run without requiring model downloads or HSBC PDFs.
