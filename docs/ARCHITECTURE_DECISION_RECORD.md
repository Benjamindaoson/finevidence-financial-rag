# Architecture Decision Record: Evidence Backend v1

## Decision

Expose the existing evidence-first primitives through a thin FastAPI adapter
with a versioned `EvidenceObject` contract. Keep retrieval, alignment,
independent coverage, and provenance in the service layer; keep Agent
planning and answer generation outside this repository boundary.

## Why

The project already has tested internal `Evidence`, `RequirementGraph`,
alignment, and coverage contracts. A stable external object makes those
capabilities callable without coupling a research Agent to benchmark classes
or Pydantic internals. The boundary also makes unsupported ACL filtering fail
closed instead of pretending that post-filtering is authorization.

## Trade-offs

- The first service uses the existing in-memory CPU HybridRetriever and is
  suitable for local integration, not a scale or availability claim.
- Table queries are metadata-first over available table evidence; they do not
  create a new verified TableIR implementation.
- PDF parsing, model serving, authentication, rate limiting, and persistence
  remain deployment concerns. Ignored local HSBC artifacts are loaded only
  when present.
- Docker is a reproducible local packaging path and intentionally excludes
  PDFs and model weights.

## Rejected scope

No Agent framework, UI, Kubernetes, Redis, GraphRAG, or new benchmark is added
as part of this backend contract.
