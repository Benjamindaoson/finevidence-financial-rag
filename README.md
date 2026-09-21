# FinEvidence

**Financial RAG & Evidence Intelligence Platform**

FinEvidence is a financial-document RAG system built around a simple rule:
retrieval relevance is not enough. A financial answer should use evidence with
the correct structure, scope and provenance, and the system should be able to
measure when required evidence is still missing.

The repository consolidates the reusable RAG capabilities that previously lived
across `finevidence-financial-rag` and `financial-asset-qa-system`. Product-
specific stock dashboards, technical indicators and investment workflows are
deliberately excluded.

## Core architecture

```text
Financial documents
        |
        v
1. Structure-aware Chunking
   - section context
   - table-atomic evidence
   - financial metadata
        |
        v
2. Hybrid Retrieval
   - Dense
   - BM25
   - RRF
   - targeted / failure-aware recovery
        |
        v
3. Reranking
   - Cross-Encoder (optional)
   - financial facets
   - hard-negative handling
   - provenance
   - coverage novelty
        |
        v
4. Evidence Qualification
   - requirement graph
   - fact-evidence alignment
   - independent coverage
   - answer eligibility
        |
        v
5. Evaluation
   - Recall / MRR / nDCG
   - hard negatives
   - evidence coverage
   - failure traces
```

## Four RAG pillars

### 1. Chunking / knowledge organization

FinEvidence provides a structure-aware chunker that keeps tables atomic and
preserves section context plus typed financial semantics:

- entity;
- metric;
- period;
- currency;
- unit;
- accounting basis;
- segment;
- consolidation scope;
- source type;
- document / page / table / row / column provenance.

This is designed to reduce failures where the retrieved number is plausible but
belongs to the wrong year, basis, unit, segment or scope.

### 2. Retrieval

The default text retrieval path is now:

```text
Dense retrieval
      +
BM25 retrieval
      |
      v
Reciprocal Rank Fusion
```

Historical weighted-fusion experiments remain reproducible through the legacy
`alpha` parameter.

FinEvidence also contains bounded targeted retrieval, structured table
retrieval, optional visual retrieval and failure-aware routing for:

- text retrieval misses;
- table structure loss;
- page fragmentation;
- layout-dependent questions;
- visual-only evidence.

### 3. Reranking

FinEvidence supports three levels of ranking:

- deterministic financial-facet reranking;
- hard-negative-aware reranking;
- optional Cross-Encoder reranking using a pluggable scorer.

The consolidated finance-aware multi-objective reranker combines:

```text
semantic relevance
+ financial facet match
+ source provenance
+ evidence coverage novelty
```

The real Cross-Encoder dependency is optional so the core CPU test suite does
not download model weights.

### 4. Evaluation

The evaluation layer treats retrieval and evidence sufficiency as different
problems. Implemented metrics include:

- Recall@K;
- MRR;
- nDCG;
- Complete Evidence Rate;
- Hard Negative Error Rate;
- required-fact precision / recall;
- critical-fact recall;
- financial facet accuracy;
- false answer eligibility rate.

The repository also keeps frozen manifests, run artifacts, failure cases and
scope/limitation notes so measured results are not mixed with unverified claims.

## Evidence intelligence layer

Beyond the four standard RAG stages, FinEvidence contains:

- typed evidence requirements;
- requirement dependency graphs;
- fact-evidence alignment;
- independent evidence reuse policy;
- critical coverage gates;
- explicit partial / insufficient evidence states;
- provenance-aware citation and verification API contracts.

A high similarity score alone never satisfies an evidence requirement.

## Repository layout

```text
src/finevidence/
├── chunking/        structure-aware and table-aware chunking
├── retrieval/       dense, BM25, RRF, targeted and multimodal retrieval
├── ranking/         financial facets, hard negatives, Cross-Encoder adapters
├── evidence/        requirements, alignment, coverage, TableIR
├── contracts/       typed evidence and benchmark contracts
├── eval/            retrieval and evidence evaluation
└── api/             evidence backend API

benchmarks/          frozen fixtures and benchmark slices
configs/             reproducible experiment configurations
docs/                architecture, evaluation and consolidation notes
reports/             measured experiment reports
tests/               unit, regression and contract tests
```

## Current measured evidence

Historical reports in this repository include, among others:

- RealFinance-v1 dense and hybrid retrieval baselines;
- HSBC natural hard-negative ranking experiments;
- independent evidence coverage and invalid-reuse analysis;
- HSBC table-structure recovery experiments;
- multimodal control experiments.

**Important:** v0.2 changed the default hybrid retrieval implementation to
Dense + BM25 + RRF and added new chunking/reranking code. Historical benchmark
numbers remain valid only for the revision that produced them. Metrics affected
by this consolidation must be rerun before being presented as v0.2 results.

See:

- `docs/RAG_CAPABILITY_AND_EVAL_MATRIX.md`
- `docs/RESUME_SAFE_METRICS.md`
- `docs/FINAL_RESUME_METRICS.md`
- `docs/CONSOLIDATION.md`

## Quick start

Requires Python 3.12+.

```bash
python -m venv .venv
python -m pip install -e '.[dev]'
python -m pytest -q
```

Optional real Cross-Encoder support:

```bash
python -m pip install -e '.[neural-rerank]'
```

Optional PDF / visual paths:

```bash
python -m pip install -e '.[pdf,visual]'
```

Run the small CPU evaluation fixture:

```bash
python -m finevidence.eval.run --config configs/mini_cpu.json
```

Start the evidence backend:

```bash
python -m uvicorn finevidence.api.app:app --host 127.0.0.1 --port 8000
```

## Deliberate boundaries

FinEvidence does not claim:

- production banking deployment;
- investment advice;
- production-scale SLA or throughput;
- neural-reranker quality gains before the real model experiment is run;
- semantic table-cell accuracy without verified cell-level gold;
- final answer / citation / abstention quality without the corresponding
  verified labels.

Missing experiments remain N/A rather than being replaced with synthetic
performance claims.
