## Context

The first P0 run established two facts on the frozen MiniBench-v1: B1 hybrid plus generic reranking slightly improved retrieval, while Hard-Negative Error remained 0.70. B2's complete-evidence number tracked retrieval recall because `required_evidence` was a flat list and the runner did not model facts, missing-fact queries, or eligibility separately.

This change narrows the project to two experiments. MiniBench-v1 remains immutable. New datasets provide fact-level completeness and a larger ranking confusion set, both using the existing Evidence IR and runner artifact conventions.

## Goals / Non-Goals

**Goals:**

- Represent each required fact with acceptable evidence alternatives and calculate a fact coverage matrix.
- Compare initial retrieval, coverage-gated eligibility, and deterministic targeted re-retrieval with at most two rounds.
- Produce Initial CER, Final CER, Partial-to-Complete Recovery, and FAER without using generation to hide retrieval failures.
- Build 100 fixed FinanceHardSet-v1 cases across the requested confusion categories.
- Compare generic, facet-aware, and hard-negative-aware ranking on identical cases and metrics.
- Persist per-query and per-round traces for replay and failure attribution.

**Non-Goals:**

- Do not modify MiniBench-v1 or enter B3 visual retrieval.
- Do not add an Agent loop, GraphRAG, external LLM/VLM, fine-tuning service, FastAPI, ACL, or Kubernetes.
- Do not call the deterministic facet ranker a neural reranker; the neural adapter remains a later experiment.

## Decisions

### 1. Backward-compatible fact schema

`MiniCase.required_facts` accepts the existing string form for frozen MiniBench-v1 and a new `FactRequirement` form for EvidenceCompleteness-v1. The coverage module normalizes both into fact records. This avoids mutating the frozen fixture while establishing the new contract.

### 2. Fact coverage before answer eligibility

Coverage is calculated as facts, not evidence IDs. A fact is covered when at least one acceptable evidence ID is selected. B2 eligibility requires all facts for answerable cases; Top-K eligibility is deliberately configurable as `any_fact` to measure FAER. No generation is needed to prove the gate decision.

### 3. Deterministic targeted retrieval

The targeted adapter receives `CoverageResult.missing_facts`, creates one query per missing fact using its description plus the original query, retrieves through the existing HybridRetriever, merges unique Evidence IDs, and repeats until complete or two rounds are exhausted. Every round is recorded. This is controlled retrieval, not an Agent.

### 4. Facets and pairwise hard-negative adapter

Facet extraction uses an explicit, versioned lexical vocabulary for entity, metric, period, basis, segment, geography, currency, and period type. Facet-aware ranking adds facet match features to the generic score. Hard-negative-aware ranking fits a deterministic pairwise perceptron over those features using FinanceHardSet-v1 positives and negatives. Both expose their backend names and use the same evaluator.

### 5. Separate benchmark responsibilities

EvidenceCompleteness-v1 owns multi-fact sufficiency; FinanceHardSet-v1 owns ranking confusion. Each has its own manifest and result table. MiniBench-v1 remains the CI/regression fixture and is not regenerated.

## Risks / Trade-offs

- [Controlled facts may be too close to the fixture corpus] → keep benchmark roles separate and label all numbers as development-slice results.
- [Lexical facet extraction can miss paraphrases] → report extractor coverage and keep the backend name explicit; do not claim neural understanding.
- [Pairwise perceptron can overfit 100 cases] → use fixed categories, report per-category HN Error, and treat FinanceHardSet-v1 as a development benchmark until an external slice is frozen.
- [Targeted query may retrieve duplicate evidence] → merge by stable Evidence ID and preserve per-round raw results plus final unique IDs.
- [FAER can be made artificially zero by always abstaining] → report coverage and eligibility together; B2 must not be judged by FAER alone.

## Migration Plan

1. Add the new typed fact form without changing MiniBench-v1 files or hash.
2. Add the two new benchmark manifests and validate all counts/hashes before running.
3. Run the completeness table and ranking table with the same code commit and save artifacts.
4. Keep old MiniBench artifacts and add new run directories; never overwrite or rewrite old results.

Rollback is selecting the prior runner/config or ignoring the new run directories. No existing benchmark files are changed.

## Open Questions

- Which real HSBC/FinRAGBench-V slice will replace the controlled FinanceHardSet cases for an external result?
- What measured improvement threshold will be used for promotion after the first larger run? This remains intentionally open; no target number is pre-filled.
