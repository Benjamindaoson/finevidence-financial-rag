## Context

`finevidence/` is a new, independent Python project inside the research workspace. The Phase 1 audit found that existing financial RAG code can return book front matter for a semantic question and can duplicate the same source. The P0 must therefore make evidence identity and evaluation first-class before adding a production API.

The first run must work without downloading the 188 GiB FinRAGBench-V corpus or calling an external LLM/VLM. It will use a small checked-in financial fixture slice with explicit gold evidence, while keeping adapters open for a real dense model, PDF/page parsing, and visual embeddings later.

## Goals / Non-Goals

**Goals:**

- Make every retrieved item traceable to document, page, block, and optional table cell.
- Run B0 Dense, B1 Hybrid + Generic Reranker, B2 Evidence Coverage, and a conditional B3 visual path from one command.
- Save immutable-enough run inputs and outputs: config, dataset manifest, predictions, metrics, failure cases, and source commit when available.
- Keep metrics honest: an unavailable visual model or missing evidence data is `N/A`, never a fabricated score.

**Non-Goals:**

- No FastAPI, graph database, agent loop, RBAC/ABAC, version graph, Kubernetes, model training, or external judge in this change.
- No full FinRAGBench-V download; its manifest is documented, but the mini benchmark is the executable development gate.
- No claim that classical local dense vectors equal a neural embedding model; the backend name and configuration must identify the actual implementation.

## Decisions

### 1. Python standard library plus small numerical dependencies

Use Python 3.12, `pydantic`, `numpy`, and `scikit-learn` for deterministic local vectorization. `sentence-transformers` and visual encoders remain optional adapters. This keeps the first run reproducible on CPU and avoids coupling the project to a vector database. A Chroma/Milvus adapter can be added only after a measured need.

### 2. Evidence IR is the external seam

`Evidence` is a frozen Pydantic model. It carries location, modality, optional table coordinates, provenance, scores, and a content hash. Retrieval implementations return `RetrievedEvidence`, while evaluation consumes the same stable evidence identifiers. This concentrates citation and coverage logic in one deep module.

### 3. Dataset is JSONL plus manifest

Each question stores `gold_answer`, `required_evidence`, `required_facts`, `failure_type`, and `answerable`. Source documents are JSONL evidence records so the first benchmark can be reviewed without a parser or database. The manifest records file hashes and counts and is checked before a run.

### 4. Baselines are deterministic and comparable

B0 uses a dense TF-IDF/SVD representation labelled `tfidf_svd_dense` until a neural model is explicitly configured. B1 fuses dense and lexical scores and applies a generic token-overlap reranker. B2 adds per-fact evidence coverage and only changes answer eligibility; it does not silently change retrieval scores. B3 runs only when visual evidence fields and a visual adapter are present, otherwise emits `N/A` with a reason.

### 5. Run artifacts are append-only by run id

`python -m finevidence.eval.run` writes under `artifacts/runs/<run_id>/`: `config.json`, `dataset_manifest.json`, `predictions.jsonl`, `metrics.json`, and `failure_cases.jsonl`. The run id is timestamp plus a short manifest hash. Existing artifacts are never overwritten by the CLI.

## Risks / Trade-offs

- [Mini benchmark may be too small] → use it only as a development/regression gate; do not call it a public benchmark result, and promote only after the real dataset slice is frozen.
- [TF-IDF/SVD is not neural semantic retrieval] → expose the backend name in config and results; add a sentence-transformers adapter as a separate measured B0 variant.
- [Fixture page numbers are synthetic for Markdown] → mark source type and provenance; page/cell claims are only valid for records with explicit coordinates.
- [B2 coverage depends on gold fact decomposition] → require every answerable case to define `required_facts`; report missing annotations instead of treating them as covered.
- [Pydantic/numpy/scikit-learn versions drift] → pin dependencies, record Python/package versions in config, and validate the manifest before evaluating.

## Migration Plan

1. Run the checked-in MiniBench with the default CPU configuration and inspect all artifacts.
2. Replace or extend the source JSONL with a fixed real document slice without changing the Evidence IR.
3. Add a neural dense adapter and real page/image ingestion as new baseline variants; keep existing run artifacts immutable.
4. If a new format is needed, write a manifest migration and retain the old fixture for regression.

Rollback is deleting or ignoring a new run directory; source data and prior runs are not modified by the runner.

## Open Questions

- Which legally redistributable HSBC/FinRAGBench-V slice will be frozen for the first public result?
- Which neural dense and visual encoders can run within the available local GPU/CPU budget?
- What exact PDF parser output will supply trustworthy page/block/bbox coordinates?
