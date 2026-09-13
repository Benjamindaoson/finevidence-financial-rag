# FinEvidence Current State Audit

Date: 2026-09-14
Audit commit: `b7c065fa565cc2a673569864b154d7f7690ec76b`
Status: read-only baseline audit for B5

## 1. Runtime and repository

- Repository: `D:\01_work\Enterprise Multimodal RAG\finevidence`
- Branch: `master`
- Working tree: clean at audit start
- Python: 3.12.10
- PyTorch: 2.8.0+cpu
- CUDA: unavailable (`torch.cuda.is_available() == False`, no `nvidia-smi`)
- Transformers: 4.55.4
- huggingface-hub: 0.34.4
- RAM: approximately 32 GiB
- Local model cache includes `Qwen/Qwen3-Embedding-0.6B`, BGE models, and SmolLM2; cache presence is not yet proof that each model can execute in this environment.

## 2. Current retrieval path

The current primary path is:

```text
Evidence records
  -> DenseRetriever (character TF-IDF + optional TruncatedSVD)
  -> HybridRetriever (dense score + lexical token overlap)
  -> deterministic facet ranking where the experiment selects it
  -> Evidence alignment
  -> independent / critical coverage
```

`DenseRetriever` is deliberately named `tfidf_svd_dense`; it is not a neural embedding model. `HybridRetriever` uses the current dense score and a generic lexical overlap score. Scores are deterministic and tie-broken by evidence ID.

`FacetAwareReranker` and `HardNegativeAwareReranker` apply explicit financial facet features for entity, metric, period, basis, segment, geography, currency, and period type. The hard-negative adapter uses deterministic pairwise weight updates. It is not a learned neural reranker.

## 3. Visual and table paths

The visual adapter is `ClipImageEncoder` plus `VisualRetriever`:

- OpenAI CLIP RN50
- real image encoding of rendered page images
- CPU in the recorded B3/B4 experiments
- page-level visual evidence; no verified bbox gold in the historical visual benchmarks

The table path contains two distinct layers:

- `T1 Parsed Page Text`: text retrieval over parsed page text; it is not structured Table IR.
- `T2 Real Structured Table IR`: bounded geometry-assisted PDF extraction with cell identity, row/column IDs, header paths, and optional bbox. Semantic cell accuracy, merged-cell accuracy, and unit accuracy remain `N/A` without human-verified gold.

## 4. Evidence qualification

`Requirement`, `RequirementGraph`, `FactEvidenceAlignment`, `EvidenceReusePolicy`, and `IndependentCoverageResult` are the current domain contracts. Visual/table candidates are not trusted merely because they were retrieved. They pass through lexical/slot alignment, reuse policy, derived-fact propagation, critical coverage, and answer eligibility.

The current graph implementation is an in-memory Pydantic DAG. It is not GraphRAG and does not use Neo4j.

## 5. Failure attribution and controlled escalation

Existing B3/B4 routing uses deterministic question cues, initial coverage, parser availability, and explicit failure categories. Supported actions include text retry, adjacent-page retrieval, structured table retrieval, visual retrieval, and abstention/escalation. B4's controller is a bounded deterministic experimental route, not an open-ended agent framework.

## 6. Frozen datasets and results

The following historical results are immutable baselines and must not be overwritten:

- RealFinance-v1: Dense Recall@5 `0.0900`; Hybrid Recall@5 `0.1417`; Hybrid Complete Evidence Rate `0.0500`.
- Gold-fact targeted retrieval: Final CER `0.8900`, FAER `0.0000`.
- P0-G D3: Raw Self Coverage `1.0000` vs Independent CER `0.7283`; Invalid Evidence Reuse Rate `0.4100`.
- P0-H: model-assisted adjudicated Requirement Recall for D4 `0.7222`; this is not human gold.
- B3.2: HSBC natural control T0 R@10 `0.5375`, T1 Parsed Page Text `0.5875`, V0 CLIP `0.0750`, M1 `0.5625`; public FinRAGBench-V page-image closure remains blocked.
- B4.1: TableIR structure recoverability `0.7418`; semantic table metrics `N/A`.
- P0-J: citation, table semantic, and answerability formal metrics remain `N/A` because no human-verified annotations exist.

Frozen public references include `RealFinance-v1`, `FinanceHardSet-v1`, `HSBCVisualStress-v1`, `HSBCNaturalMultimodal-v1`, `HSBCMultimodalRouting-v1`, `FinRAGBench-V-Slice-v1`, and their manifests. B5 must create new run directories and must never mutate prior result JSON.

## 7. Existing API and backward compatibility

Evidence Backend v1 is a FastAPI wrapper around search, coverage, table query, verification, citation, and review-workbench operations. The stable evidence contract is `Evidence`; the external API contract is `EvidenceObject` with provenance, financial metadata, structure, visual reference, and verification status.

B5 adapters must remain outside the core domain contracts. Existing `Evidence`, `Requirement`, coverage, citation, and API schemas remain backward compatible. New retrievers may implement a small common adapter protocol, but model names must not leak into Evidence IR.

## 8. Current technical debt relevant to B5

1. Dense retrieval is a CPU TF-IDF/SVD baseline, not neural retrieval.
2. Generic hybrid scoring mixes heterogeneous signals without a modern learned reranker.
3. No late-interaction index exists.
4. CLIP RN50 is the only visual model; ColPali/ColQwen is absent.
5. Existing T1 is parsed page text, not verified structured table IR.
6. Facet vocabulary and extraction are deterministic and narrow.
7. Evidence alignment is deterministic lexical/slot alignment, not a neural entailment verifier.
8. No typed B5 controller or lightweight evidence graph exists.
9. P0-J still needs human verification for formal trust metrics.
10. FinRAGBench-V page-image evaluation is blocked by the large public archive transfer.

## 9. Reuse decisions

Reuse:

- `Evidence`, `RetrievedEvidence`, Requirement Graph, alignment, coverage, failure taxonomy, and provenance contracts.
- Existing `HybridRetriever` as the BM25/keyword-compatible baseline until a separately named BM25 adapter is justified.
- Existing fusion, routing, table IR, PDF rendering, benchmark loader, and evaluation metric primitives.
- Frozen benchmark manifests and historical artifact directories.

Add only when an experiment requires it:

- neural dense adapter for the cached Qwen model;
- neural reranker adapter if a runnable local model and compatible contract are available;
- late-interaction adapter only after a bounded viability check;
- modern visual adapter only if a runnable image-consuming model is available;
- typed controller and graph only after the corresponding retrieval evidence is measured.

## 10. Audit boundary

This audit establishes the starting state. It does not claim that cached Qwen, ColBERT, or visual models execute successfully, nor that any proposed B5 module improves a frozen benchmark. Those are experimental questions for B5.1 onward.
