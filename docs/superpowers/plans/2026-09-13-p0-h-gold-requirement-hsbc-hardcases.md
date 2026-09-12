# P0-H Gold Requirement & HSBC Hard Cases Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate P0-G on a model-assisted adjudicated requirement subset and a provenance-fixed, naturally mined HSBC financial hard-case set.

**Architecture:** Preserve the frozen RealFinance-v1/P0-G contracts and add a thin annotation/evaluation layer plus a bounded local-LLM adapter. Add a source-hash-checked HSBC download/parser/miner path that emits Evidence IR blocks and ranking cases; keep artifacts separate and keep B3 itself unimplemented.

**Tech Stack:** Python 3.12, Pydantic 2, scikit-learn, existing Evidence IR/HybridRetriever, optional local Transformers + PyTorch, PowerShell, pytest, OpenSpec, CodeGraph.

**Spec:** `openspec/changes/p0-h-gold-requirement-hsbc-hardcases/`

## Global Constraints

- `RequirementAdjudicated-v1` is model-assisted, not human gold: `human_verified=false`.
- `HSBCNaturalHard-v1` is project-created from public HSBC disclosure blocks, not an HSBC-official benchmark.
- Do not modify RealFinance-v1, TAT-QA or FinQA source data.
- Do not add GraphRAG, Neo4j, agents, ACL, FastAPI, Kubernetes, visual retrieval or full FinRAGBench-V.
- Do not fabricate annotations, model outputs, hard negatives or benchmark scores.

---

### Task 1: Contracts, annotation provenance and one-to-one matching

**Files:**
- Create: `src/finevidence/contracts/p0_h.py`
- Create: `src/finevidence/eval/p0_h_annotation.py`
- Create: `tests/test_p0_h_annotation.py`

**Interfaces:**
- `RequirementAnnotationCase`, `RequirementAnnotationPass`, `RequirementAdjudicatedCase`, `P0HAnnotationManifest`.
- `match_requirements(predicted, adjudicated) -> RequirementMatchResult`.
- `build_requirement_adjudicated_subset(benchmark, case_ids, output_dir) -> P0HAnnotationManifest`.

- [ ] Write tests for provenance flags, dual-pass disagreement retention, and one-to-one matching.
- [ ] Run the focused tests and confirm they fail because the new contracts/functions are absent.
- [ ] Implement only the contracts and deterministic matching needed by the tests.
- [ ] Run focused tests and confirm they pass.
- [ ] Commit: `git commit -m "Add P0-H annotation contracts and matching"`.

### Task 2: D1 local model adapter and D0–D4 annotation evaluation

**Files:**
- Create: `src/finevidence/evidence/llm_direct.py`
- Create: `src/finevidence/eval/p0_h_requirements.py`
- Create: `tests/test_p0_h_llm.py`
- Modify: `src/finevidence/evidence/fact_understanding.py`

**Interfaces:**
- `LocalLLMConfig` and `run_direct_decomposition(question, config) -> DecompositionResult`.
- `evaluate_requirement_methods(cases, annotations, config) -> dict`.

- [ ] Write tests for valid JSON, one bounded malformed JSON retry, and explicit N/A metadata.
- [ ] Run focused tests and confirm RED.
- [ ] Implement local Transformers loading with greedy generation and schema validation; keep missing dependency/model as N/A.
- [ ] Run focused tests and one real cached-model probe; record exact provenance or blocker.
- [ ] Commit: `git commit -m "Add D1 direct decomposition baseline"`.

### Task 3: HSBC corpus download, provenance and minimal parser

**Files:**
- Create: `src/finevidence/benchmarks/hsbc.py`
- Create: `scripts/build_hsbc_corpus.py`
- Create: `tests/test_hsbc_p0_h.py`
- Modify: `.gitignore`

**Interfaces:**
- `download_hsbc_corpus(source_manifest, output_dir) -> dict`.
- `parse_hsbc_pdf(path, document_manifest) -> list[Evidence]`.
- `validate_hsbc_manifest(manifest) -> None`.

- [ ] Write tests for SHA/page metadata, ignored PDF paths and rejection of non-manifest candidate text.
- [ ] Run focused tests and confirm RED.
- [ ] Implement URL download with timeout, SHA-256 and a minimal text/page parser using an available PDF library or explicit technical N/A per file.
- [ ] Run the official HSBC download and parser; retain PDFs only under ignored artifacts.
- [ ] Commit: `git commit -m "Add HSBC provenance corpus pipeline"`.

### Task 4: HSBC natural hard-case mining and ranking

**Files:**
- Create: `src/finevidence/eval/p0_h_hsbc.py`
- Create: `tests/test_hsbc_hardcases.py`
- Create: `configs/p0_h_cpu.json`

**Interfaces:**
- `mine_hsbc_natural_hard_cases(evidence, target_count=50) -> list[HSBCHardCase]`.
- `evaluate_hsbc_ranking(cases, evidence) -> dict`.

- [ ] Write tests for positive/negative/facet conflict gates and predicted/gold facet separation.
- [ ] Run focused tests and confirm RED.
- [ ] Implement conservative mining from parsed blocks only; drop ambiguous cases.
- [ ] Run ranking and category metrics; report counts, not only aggregates.
- [ ] Commit: `git commit -m "Add HSBC natural hard-case evaluation"`.

### Task 5: P0-H runner, report, reproducibility and gate

**Files:**
- Create: `src/finevidence/eval/p0_h.py`
- Create: `reports/p0-h-gold-requirement-hsbc-natural-hardcases.md`
- Modify: `README.md`, `PROJECT_STRATEGY.md`, `BENCHMARK_AND_HARD_CASE_PLAN.md`, `CHAT_KNOWLEDGE_BASE.md`

**Interfaces:**
- `run_p0_h(config) -> Path`.
- Outputs: `config.json`, `dataset_manifest.json`, `annotation_manifest.json`, `requirement_annotations.jsonl`, `requirement_predictions.jsonl`, `requirement_metrics.json`, `requirement_failure_cases.jsonl`, `hsbc_corpus_manifest.json`, `hsbc_hard_cases.jsonl`, `facet_predictions.jsonl`, `ranking_predictions.jsonl`, `ranking_metrics.json`, `ranking_failure_cases.jsonl`, `per_query_trace.jsonl`, `b3_gate.json`.

- [ ] Write runner artifact and gate tests.
- [ ] Run the full verification commands and repair the first meaningful failure.
- [ ] Run P0-H twice with the same config and compare metrics, predictions, failures and manifests.
- [ ] Update all project documentation with exact boundaries and paths.
- [ ] Commit: `git commit -m "Finalize P0-H experiments and report"`.
