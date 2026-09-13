# B5 Experiment Matrix

All rows use a new B5 run directory and the frozen dataset manifest for that stage. Historical B3/B4/P0-J artifacts remain untouched.

## Retrieval ladder

| ID | System | Intervention | Expected status |
|---|---|---|---|
| R0 | BM25/keyword baseline | existing lexical component or explicit compatible adapter | baseline |
| R1 | Current Dense | TF-IDF + optional SVD | frozen baseline |
| R2 | Current Hybrid | current dense + lexical score | frozen baseline |
| R3 | Qwen Dense | real cached Qwen3 embedding adapter | viability-gated |
| R4 | Keyword + Qwen Dense | normalized union/fusion | viability-gated |
| R5 | R4 + deterministic financial facets | current deterministic ranker | baseline comparator |
| R6 | R4 + neural reranker | real cross-encoder only | viability-gated |
| R7 | R4 + late interaction | real token-level adapter only | viability-gated |
| R8 | R4 + late interaction + reranker | combined neural stack | viability-gated |

## Visual and search-control ladder

| ID | System | Intervention | Expected status |
|---|---|---|---|
| V0 | CLIP RN50 | existing real image encoder | frozen B3/B4 baseline |
| V1 | ColPali/ColQwen-style | actual image-consuming model | viability-gated |
| M0 | Text + always-on visual | normalized RRF/weighted fusion | existing comparator |
| M1 | Text + conditional visual | typed bounded routing | existing comparator / B5 extension |
| A0 | One-shot hybrid | one initial retrieval | baseline |
| A1 | Fixed decomposition | deterministic sub-query sequence | comparator |
| A2 | Fixed multi-step | fixed bounded tool sequence | comparator |
| A3 | Typed controller | coverage/failure-aware bounded actions | target intervention |
| G0 | No graph | existing retrieval | baseline |
| G1 | Typed evidence graph | in-memory cross-document lookup | viability-gated |

## Required metrics

Retrieval: Recall@1/5/10, MRR, nDCG@10, candidate overlap, unique recovery.

Evidence: Complete Evidence Rate, Independent Coverage, Critical Coverage, answer eligibility, FAER.

Hard negatives: HN Error, Top-1 accuracy, per-category entity/metric/period/basis/segment/confusion rates.

Controller: steps, queries, tool calls, coverage delta, recovery, regression, abstention, stop reason, budget use.

System: index time, index size, P50/P95 query latency, peak memory, CPU/GPU time, visual calls/pages/query, and cost proxy where defensible.

## Stage decisions

Each intervention ends with exactly one of: `PROMOTE`, `KEEP_AS_OPTIONAL`, `REJECT`, `INCONCLUSIVE`. The decision must cite the frozen benchmark, observed delta, failure categories, and cost. Model novelty alone cannot promote a component.

## Current execution status

The first B5.1 run is recorded under `artifacts/b5_1_runs/`. R1 and R2
executed on frozen `RealFinance-v1`; R3/R4 are `N/A` because the pinned Qwen
checkpoint weights were not locally available and the bounded HF/Xet fetch
did not transfer bytes. B5.2–B5.6 remain gated on a runnable model or a
separate explicitly authorized viability experiment.
