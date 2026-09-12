# P0-D Real-Finance Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a hash-verified 100-case public real-finance validation slice from TAT-QA and FinQA, then measure oracle/predicted fact completeness and gold/predicted facet ranking without touching the frozen fixtures.

**Architecture:** Keep public-source acquisition outside the package and use a deterministic adapter to project TAT-QA report tables/paragraphs and FinQA rows/sentences into the existing Evidence IR. Extend case provenance and metrics only where required; use the existing Dense, Hybrid, coverage, and targeted retrieval components. Treat missing HSBC source data as a readiness gate, not an excuse to synthesize stress results.

**Tech Stack:** Python 3.12, Pydantic, scikit-learn, JSONL, standard-library hashing, existing `.venv`.

**Spec:** `openspec/changes/p0-d-real-finance-validation/`

## Global Constraints

- Keep `MiniBench-v1`, `FinanceHardSet-v1`, and `EvidenceCompleteness-v1` byte-for-byte unchanged.
- Do not download FinRAGBench-V full corpus.
- Do not add Agent, GraphRAG, ACL, FastAPI, K8s, or visual retrieval.
- Do not use gold facts/programs as retrieval input; use them only for evaluation/provenance.
- Preserve source repo commit and raw-file hashes.
- Keep public slice results separate from controlled fixture results.

---

### Task 1: Public source manifest and raw-data audit

**Files:**
- Create: `scripts/audit_public_finance_sources.py`
- Create: `data/source_manifests/public_finance_sources.json`
- Test: `tests/test_public_source_audit.py`

- [ ] Write a failing test for source metadata fields and split counts.
- [ ] Run it and verify failure because the audit manifest does not exist.
- [ ] Implement read-only audit of `research/repos/tat-qa` and `research/repos/FinQA` without copying raw data.
- [ ] Record URL, commit, relative path, byte size, SHA-256, record counts, license note, and source schema.
- [ ] Run audit and test; stop with explicit `N/A` if either source file is missing.

### Task 2: Public record adapter and RealFinance-v1 slice

**Files:**
- Create: `src/finevidence/benchmarks/real_finance.py`
- Create: `benchmarks/real_finance_v1/questions.jsonl`
- Create: `benchmarks/real_finance_v1/evidence.jsonl`
- Create: `benchmarks/real_finance_v1/manifest.json`
- Test: `tests/test_real_finance_adapter.py`

- [ ] Write failing tests for TAT-QA table-text mapping and FinQA `gold_inds`/program preservation.
- [ ] Run tests and verify failure because the adapter is absent.
- [ ] Implement deterministic conversion and fixed selection of 50 TAT-QA + 50 FinQA cases from committed source hashes.
- [ ] Validate derived evidence content hashes and source IDs.
- [ ] Run adapter tests and manifest verification.

### Task 3: Required Fact Decomposer and facet evaluation

**Files:**
- Create: `src/finevidence/evidence/decomposition.py`
- Modify: `src/finevidence/ranking/facets.py`
- Modify: `src/finevidence/eval/metrics.py`
- Test: `tests/test_fact_decomposition.py`, `tests/test_facet_evaluation.py`

- [ ] Write failing tests for omitted-fact recall and paraphrased facet misses.
- [ ] Implement deterministic baseline decomposer and per-field exact-match metrics.
- [ ] Add oracle/predicted fact conditions and gold/predicted facet ranking labels.
- [ ] Run focused tests and confirm explicit denominators.

### Task 4: RealFinance runner and HSBC readiness gate

**Files:**
- Create: `src/finevidence/eval/p0_d.py`
- Create: `configs/p0_d_cpu.json`
- Create: `tests/test_p0_d_runner.py`
- Modify: `README.md`

- [ ] Write failing tests for separate public-slice tables, provenance, and HSBC `N/A` gate.
- [ ] Implement one runner that emits source/derived manifests, per-query traces, ranking/sufficiency tables, facet metrics, and readiness status.
- [ ] Run the same config twice and compare stable metrics/manifests.
- [ ] Run full tests, OpenSpec strict validation, CodeGraph status, and Git status.

### Task 5: External validity report

**Files:**
- Create: `reports/p0-d-real-finance-validation.md`
- Modify: top-level `CHAT_KNOWLEDGE_BASE.md`, `PROJECT_STRATEGY.md`, `BENCHMARK_AND_HARD_CASE_PLAN.md`

- [ ] Report public source facts with links, source commits/hashes, exact commands, output paths, observed metrics, and limitations.
- [ ] Keep unavailable HSBC stress results as `N/A`.
- [ ] Do not promote controlled fixture numbers into external-validity claims.
