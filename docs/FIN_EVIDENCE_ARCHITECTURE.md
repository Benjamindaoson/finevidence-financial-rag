# FinEvidence Evidence Backend v1 Architecture

## Current verified architecture

```text
Financial documents
        ↓
Existing parsers / page rendering / TableIR extraction
        ↓
Evidence IR
        ↓
Text, TableIR-cell, or visual retrieval
        ↓
Fact–evidence alignment
        ↓
Independent / critical coverage
        ↓
Benchmark evaluation and reproducibility artifacts
```

The current repository is primarily an evidence-first experiment harness. `src/finevidence/eval/` contains benchmark runners and must not be mistaken for a service boundary. The reusable backend primitives are the immutable `Evidence` contract, `TableIR`, retrievers, requirement decomposition, alignment, independent coverage, citation helpers, and HSBC provenance loaders.

The source-backed architecture diagram is [financial-evidence-backend.architecture.json](architecture/financial-evidence-backend.architecture.json), with the validated standalone viewer at [financial-evidence-backend.architecture.html](architecture/financial-evidence-backend.architecture.html).

## Evidence Backend v1 target boundary

```text
AI Research Agent
        ↓  HTTP / JSON
Evidence API
        ↓
Evidence Service
        ↓
Retrieval engines (text / TableIR / visual)
        ↓
Stable EvidenceObject responses
        ↓
Verification: alignment + coverage + citation
```

The service is deliberately a thin adapter. It does not contain an Agent loop, PDF parser implementation, model-serving platform, UI, or production distributed storage. The service loads the ignored local HSBC page catalog when the provenance, render, and evidence artifacts are present; otherwise it starts with an empty catalog and can receive an injected catalog in tests.

## Trust and ownership boundaries

- Documents and local artifacts are source inputs; their hashes remain provenance data.
- Retrieval proposes evidence; it does not grant answer eligibility.
- Verification decides whether a claim is supported and whether critical requirements are covered.
- The external Agent owns planning, reasoning, and memo composition. It must not silently replace FinEvidence verification with its own PDF parsing or unsupported claims.
- The API contract is versioned separately from the internal `Evidence` Pydantic model so future internal refactors do not silently break Agent clients.

## Explicit non-goals

This release does not claim full enterprise ACL enforcement, semantic financial-fact extraction, conflict adjudication, or production-scale persistence. The contract is ACL-ready through request filters and an authorization hook, but default local development behavior is fail-closed when a caller supplies a security filter that the catalog cannot enforce.
