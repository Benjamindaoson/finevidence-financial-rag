# B5 Design

## Boundary

Model adapters produce `RetrievedEvidence`; they do not change `Evidence`,
`Requirement`, `RequirementGraph`, `FactEvidenceAlignment`, or coverage
contracts. The controller consumes those domain objects and emits typed,
provenance-bearing search actions and stop reasons.

## Stage contracts

1. B5.1 neural dense: model-backed text embeddings, explicit checkpoint and
   runtime manifest, same corpus and qrels as the current baseline.
2. B5.2 reranking: a true pair/query-document model only; deterministic facet
   ranking remains separately named.
3. B5.3 late interaction: token-level query/document representations and a
   documented interaction score; lexical overlap is not an implementation.
4. B5.4 visual: image-consuming model over deterministic page renders;
   results re-enter alignment and critical coverage.
5. B5.5 controller: bounded typed actions for text/table/visual/graph with
   coverage delta, failure cause, budget, and stop reason.
6. B5.6 graph: typed in-memory nodes/edges only, added only for measured
   cross-document gaps.

## Reproducibility

Each stage records code commit, dataset manifest/hash, model manifest,
configuration, seed, metrics, per-case rows, latency, cost proxy, and failure
rows in a fresh run directory. Historical result directories are read-only
inputs.

## Failure semantics

An unavailable model is not silently replaced by a heuristic with the same
name. It is recorded as `N/A` with the attempted runtime/checkpoint and the
technical reason. Neural claims require an executed neural model path.
