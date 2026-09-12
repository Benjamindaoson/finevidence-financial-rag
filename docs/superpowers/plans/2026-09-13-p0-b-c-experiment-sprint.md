# P0-B/P0-C Experiment Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prove fact-level evidence sufficiency and financial hard-negative ranking on two fixed development suites without entering B3 or adding new platform modules.

**Architecture:** Extend the existing contracts compatibly, add fact coverage and bounded targeted retrieval as internal evidence modules, and add explicit facet/pairwise ranking adapters under the existing retrieval/evaluation flow. A single sprint runner writes per-query/per-round traces and two summary tables into a new run directory.

**Tech Stack:** Existing Python 3.12, Pydantic, NumPy, scikit-learn, pytest, JSONL, and standard-library hashing.

**Spec:** `openspec/changes/p0-b-c-experiment-sprint/`

## Global Constraints

- `benchmarks/mini_finance/` is frozen; do not modify its files or manifest.
- Do not add B3, GraphRAG, Agent, ACL, FastAPI, K8s, external LLM/VLM, or training service.
- All values come from fixed manifests and actual runs; unavailable metrics remain `N/A`.
- Targeted retrieval is deterministic and capped at two rounds.
- Every new production behavior has a failing test first.

---

### Task 1: Fact schema and coverage matrix

**Files:**
- Modify: `src/finevidence/contracts/benchmark.py`
- Modify: `src/finevidence/evidence/coverage.py`
- Modify: `tests/test_contracts.py`
- Modify: `tests/test_evaluation.py`

**Interfaces:**
- `FactRequirement(fact_id, description, acceptable_evidence_ids)`
- `fact_coverage_for_case(case, selected_ids) -> FactCoverageResult`
- `false_answer_eligibility_rate(cases, eligibility) -> float | str`
- `complete_evidence_rates(initial, final) -> dict`

- [ ] Write failing tests for alternative evidence, fact coverage, FAER, and initial/final/recovery rates.
- [ ] Run the focused tests and verify the intended red failures.
- [ ] Implement backward-compatible fact normalization for MiniBench-v1 string facts.
- [ ] Run focused and full tests; confirm MiniBench-v1 hash is unchanged.

### Task 2: EvidenceCompleteness-v1 and bounded targeted retrieval

**Files:**
- Create: `benchmarks/evidence_completeness_v1/questions.jsonl`
- Create: `benchmarks/evidence_completeness_v1/manifest.json`
- Create: `src/finevidence/retrieval/targeted.py`
- Modify: `src/finevidence/benchmarks/loader.py`
- Create: `tests/test_targeted_retrieval.py`

**Interfaces:**
- `TargetedRetrievalResult(initial, final, selected_ids, rounds)`
- `TargetedRetriever.retrieve(case, original_query, top_k, max_rounds=2)`

- [ ] Write failing tests for missing-fact query construction, one-round recovery, and two-round cap.
- [ ] Run focused tests and verify red.
- [ ] Add 30–50 multi-evidence cases without editing MiniBench-v1.
- [ ] Implement bounded merge-and-recheck trace.
- [ ] Run focused/full tests and verify both manifests.

### Task 3: Financial facet and hard-negative ranking

**Files:**
- Create: `src/finevidence/ranking/facets.py`
- Create: `src/finevidence/ranking/rerankers.py`
- Create: `benchmarks/finance_hardset_v1/questions.jsonl`
- Create: `benchmarks/finance_hardset_v1/manifest.json`
- Create: `tests/test_financial_ranking.py`

**Interfaces:**
- `extract_facets(query) -> FinancialFacets`
- `FacetAwareReranker.rank(query, candidates, evidence_by_id, top_k)`
- `HardNegativeAwareReranker.fit(cases, evidence_by_id)`
- `HardNegativeAwareReranker.rank(query, candidates, evidence_by_id, top_k)`

- [ ] Write failing tests for facet extraction, facet matching, reproducible pairwise fit, and category scoring.
- [ ] Run focused tests and verify red.
- [ ] Add exactly 100 fixed hard-negative cases across the frozen category list.
- [ ] Implement explicit facet features and deterministic pairwise weight fitting.
- [ ] Run focused/full tests and verify manifest counts/hashes.

### Task 4: Sprint runner, traces, and results

**Files:**
- Create: `src/finevidence/eval/p0_bc.py`
- Create: `configs/p0_bc_cpu.json`
- Create: `tests/test_p0_bc_runner.py`
- Modify: `README.md`

**Interfaces:**
- `python -m finevidence.eval.p0_bc --config configs/p0_bc_cpu.json`
- Writes `ranking_table.json`, `sufficiency_table.json`, `per_query_trace.jsonl`, plus standard config/manifest/metrics/failures.

- [ ] Write failing tests for required summary tables, trace round fields, and commit metadata.
- [ ] Run focused tests and verify red.
- [ ] Implement one runner that does not invoke visual retrieval.
- [ ] Run the sprint command twice and compare manifest, commit, and metrics stability.
- [ ] Run all tests, OpenSpec strict validation, CodeGraph status, and Git status before reporting results.
