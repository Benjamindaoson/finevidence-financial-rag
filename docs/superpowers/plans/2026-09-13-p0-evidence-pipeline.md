# P0 Evidence Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the smallest reproducible FinEvidence loop that runs B0 Dense, B1 Hybrid + Generic Reranker, B2 Evidence Coverage, and an honest conditional B3 Visual result over a fixed MiniBench.

**Architecture:** A JSONL Evidence IR is the seam between ingestion fixtures, retrieval, ranking, coverage, and evaluation. A CLI loads and verifies the manifest, runs each baseline over the same corpus, and writes immutable run artifacts. Visual retrieval is an optional adapter and reports `N/A` when the fixture or encoder is unavailable.

**Tech Stack:** Python 3.12, Pydantic, NumPy, scikit-learn, pytest, standard-library JSONL and hashing.

**Spec:** `openspec/changes/p0-evidence-pipeline/`

## Global Constraints

- Do not modify any repository under `../research/repos/`.
- Do not download the full FinRAGBench-V corpus.
- Do not claim a neural embedding result for the CPU `tfidf_svd_dense` adapter.
- Do not fill unavailable metrics with zero; use `N/A` and a reason.
- Every new production function gets a failing test before implementation.

---

### Task 1: Evidence IR and manifest contracts

**Files:**
- Create: `src/finevidence/contracts/evidence.py`
- Create: `src/finevidence/contracts/benchmark.py`
- Create: `tests/test_contracts.py`

**Interfaces:**
- `Evidence.from_content(document_id, source_uri, page, block_id, modality, text, **metadata) -> Evidence`
- `Evidence.content_hash: str`
- `MiniCase` and `RequiredEvidenceRef` typed models

- [ ] Write failing tests for deterministic hashing, hash mismatch rejection, and required evidence validation.
- [ ] Run `pytest tests/test_contracts.py -q` and confirm failure because modules do not exist.
- [ ] Implement only the Pydantic models and validators required by the tests.
- [ ] Run the focused tests and then `pytest -q`.

### Task 2: Fixed MiniBench fixture and manifest

**Files:**
- Create: `benchmarks/mini_finance/evidence.jsonl`
- Create: `benchmarks/mini_finance/questions.jsonl`
- Create: `benchmarks/mini_finance/manifest.json`
- Create: `src/finevidence/benchmarks/loader.py`
- Create: `tests/test_benchmark_loader.py`

**Interfaces:**
- `load_benchmark(root: Path) -> Benchmark`
- `verify_manifest(root: Path) -> None`

- [ ] Write failing tests for valid loading, changed-file rejection, and unanswerable cases.
- [ ] Run the focused tests and confirm the expected missing-module failure.
- [ ] Add a compact fixture with text, table, visual-caption, hard-negative, cross-evidence, and unanswerable cases.
- [ ] Implement JSONL loading, SHA-256 manifest verification, and count checks.
- [ ] Run focused and full tests.

### Task 3: B0/B1/B3 retrieval adapters

**Files:**
- Create: `src/finevidence/retrieval/dense.py`
- Create: `src/finevidence/retrieval/hybrid.py`
- Create: `src/finevidence/retrieval/visual.py`
- Create: `tests/test_retrieval.py`

**Interfaces:**
- `DenseRetriever.fit(evidence: list[Evidence]) -> None`
- `DenseRetriever.search(query: str, top_k: int) -> list[RetrievedEvidence]`
- `HybridRetriever.search(query: str, top_k: int) -> list[RetrievedEvidence]`
- `VisualRetriever.available: bool`

- [ ] Write failing tests for traceable top-k results, deterministic ordering, hybrid score fusion, and unavailable visual state.
- [ ] Run focused tests and confirm red.
- [ ] Implement CPU TF-IDF/SVD dense retrieval, lexical fusion, and an explicit visual adapter that is `N/A` without visual fields/encoder.
- [ ] Run focused tests and full tests.

### Task 4: Evidence coverage and hard-negative evaluation

**Files:**
- Create: `src/finevidence/evidence/coverage.py`
- Create: `src/finevidence/eval/metrics.py`
- Create: `tests/test_evaluation.py`

**Interfaces:**
- `coverage_for_case(case: MiniCase, selected_ids: set[str]) -> CoverageResult`
- `hard_negative_error_rate(cases: list[MiniCase], rankings: dict[str, list[str]]) -> float | str`
- `evaluate_retrieval(...) -> dict[str, float | str]`

- [ ] Write failing tests for partial/full coverage, negative-above-positive, and missing annotation `N/A`.
- [ ] Run focused tests and confirm red.
- [ ] Implement metrics with explicit denominators and no fabricated defaults.
- [ ] Run focused tests and full tests.

### Task 5: Reproducible runner and artifacts

**Files:**
- Create: `src/finevidence/eval/run.py`
- Create: `configs/mini_cpu.json`
- Create: `tests/test_runner.py`
- Create: `README.md`

**Interfaces:**
- `python -m finevidence.eval.run --config configs/mini_cpu.json`
- writes `artifacts/runs/<run_id>/{config.json,dataset_manifest.json,predictions.jsonl,metrics.json,failure_cases.jsonl}`

- [ ] Write failing test for required artifact files and no overwrite on repeated run.
- [ ] Run focused test and confirm red.
- [ ] Implement the CLI and artifact writer; B3 must emit `N/A` when unavailable.
- [ ] Run unit tests, execute the CLI twice, and inspect both run directories.
- [ ] Run the strongest available verification command and record actual metrics only.

## Self-review checklist

- P0-A/B/C each has a baseline and a measurable metric.
- Evidence identity is available before any answer generation code exists.
- B2 changes answer eligibility, not retrieval metrics.
- B3 cannot silently pretend to be visual retrieval.
- The runner never overwrites artifacts and never fills missing data with a guessed score.
