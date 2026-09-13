# B5 Architecture

## Current implemented boundary

```text
Question
  -> existing requirement / evidence contracts
  -> current dense or hybrid retrieval
  -> optional QwenEmbeddingRetriever adapter
  -> RetrievedEvidence
  -> existing alignment and independent coverage
  -> bounded typed action selection
  -> run manifest / metrics / failure artifacts
```

The B5 adapters are deliberately outside the Evidence domain. They produce
`RetrievedEvidence`; they do not decide that a candidate is trusted. The
qualification gate remains the authority for independent and critical
coverage.

## Implemented in this increment

- `QwenEmbeddingRetriever`: real Transformers adapter with an explicit
  `N/A` state when the checkpoint cannot load.
- `TypedSearchController`: deterministic bounded tool/action selector.
- `EvidenceGraph`: typed in-memory graph with registered-node edge checks.
- B5.1 runner: frozen RealFinance-v1 comparison and fresh run artifacts.

## Not yet promoted

Neural reranking, ColBERT late interaction, ColQwen/ColPali visual retrieval,
and graph-backed retrieval have no executed B5 experiment in this environment.
They remain viability-gated rather than being represented by a heuristic
placeholder.
