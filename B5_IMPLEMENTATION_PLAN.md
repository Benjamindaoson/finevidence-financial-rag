# B5 Implementation Plan — Neural Retrieval & Controlled Agentic Search

## Objective

Measure whether modern neural retrieval and a bounded search controller improve evidence-qualified financial retrieval on frozen data, without bypassing independent coverage, critical coverage, provenance, or historical result boundaries.

## Stage order and gates

### B5.1 Neural dense retrieval

Run a viability probe for the cached `Qwen/Qwen3-Embedding-0.6B` on CPU. If it loads and consumes text, add an adapter with explicit model provenance. Compare BM25/keyword, current dense, current hybrid, Qwen dense, and keyword+Qwen. If it does not run within a bounded local resource budget, record technical `N/A` and retain the current baseline.

Gate: same cases, qrels, top-k, and metric code; report retrieval, coverage, hard-negative, and cost deltas.

### B5.2 Neural reranking

Attempt only a model/runtime that is already cached or reasonably downloadable and CPU-runnable. A Qwen embedding model alone is not a reranker. Do not label a deterministic facet score as neural. Compare the current deterministic ranker against any real neural reranker on the identical candidate union.

Gate: prove reduced hard-negative error or improved ranking, otherwise `REJECT`/`INCONCLUSIVE`.

### B5.3 Late interaction

First perform a small viability check for a token-level index using existing dependencies. Add a ColBERT-style adapter only if a real model is available and the representation is actually token-level. Report index size, overlap, unique recovery, latency, and memory. A lexical token overlap shortcut must not be called ColBERT.

Gate: independent gain on fine-grained financial confusions, not merely higher complexity.

### B5.4 Conditional visual retrieval

Keep CLIP RN50 as the historical baseline. Attempt a real ColPali/ColQwen-style image-consuming adapter only if a runnable local checkpoint exists or can be acquired within the bounded environment. Every visual result re-enters alignment and coverage. Page hit is not citation or evidence satisfaction.

Gate: category-level visual recovery minus regression, with invocation and latency cost.

### B5.5 Typed agentic search

Implement a deterministic-control-first controller only after the adapter contracts are stable. Use explicit state, typed actions, bounded budgets, coverage delta, failure attribution, and stop reasons. No LangGraph, AutoGen, CrewAI, or unconstrained LLM tool loop.

Gate: more independently covered critical requirements per unit cost, with no silent budget or provenance violations.

### B5.6 Lightweight evidence graph

Add a typed in-memory graph only if cross-document retrieval cases require it after B5.1–B5.5. Start with entity, metric, period, segment, basis, document, and evidence nodes plus provenance-bearing edges. Do not deploy a graph database.

Gate: measurable cross-document recovery that cannot be explained by existing text/facet retrieval alone.

## Non-negotiable invariants

- Historical artifacts are immutable.
- Frozen benchmarks are referenced by manifest/hash, never silently changed.
- No generated labels are called human gold.
- No model is called neural unless it actually executes the advertised model path.
- Every candidate remains provenance-bearing and evidence-qualified.
- Every stage has a new run ID, config, manifest, metrics, per-case results, latency, and failure rows.
- `N/A` is preferred to an unobserved or fabricated result.

## Planned outputs

- `B5_ARCHITECTURE.md`
- `B5_EXPERIMENT_MATRIX.md`
- `B5_RESULTS.md`
- `B5_FAILURE_ANALYSIS.md`
- `B5_COST_LATENCY.md`
- `B5_DECISIONS.md`
- stage-specific artifacts under `artifacts/b5_*_runs/`
- a B5 OpenSpec change with typed adapter, experiment, controller, and graph contracts

## Current risks

- CPU-only environment may make 0.6B neural inference expensive but still viable.
- No local Qwen reranker or late-interaction checkpoint has been confirmed.
- The public FinRAGBench-V archive remains a separate external blocker.
- P0-J formal trust metrics remain blocked on human verification.
- Existing benchmarks are mostly text/page-level; conclusions must be limited to the observed slices.
