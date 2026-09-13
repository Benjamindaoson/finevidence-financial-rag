# B5 — Neural Retrieval & Controlled Agentic Search

Date: 2026-09-14  
Status: **PARTIAL — B5.1 model-weight blocker**  
Audit/run code commit: `b7c065fa565cc2a673569864b154d7f7690ec76b`

## 1. Research question

Does modern neural retrieval provide measurable value over FinEvidence's
current CPU dense/hybrid baseline on financial evidence, while preserving the
Evidence Qualification contract? The answer is not yet measurable for Qwen in
this environment because no Qwen inference executed.

## 2. Environment and frozen data

- Windows, Python 3.12.10, approximately 32 GiB RAM.
- PyTorch 2.8.0+cpu; CUDA unavailable and `nvidia-smi` unavailable.
- Transformers 4.55.4; huggingface-hub 0.34.4; hf_xet available.
- Frozen `RealFinance-v1`: 100 cases, 1,652 evidence records, 50 TAT-QA + 50 FinQA.
- No P0–B4/P0-J historical artifact was overwritten.

## 3. Implemented contracts

The new `ModelManifest` records model, revision, runtime, device, status,
weights hash, and errors. `QwenEmbeddingRetriever` is an actual
Transformers adapter and returns no results when unavailable. `SearchAction`,
`SearchBudget`, and `SearchControllerState` provide a bounded typed control
boundary. `EvidenceGraph` is an in-memory typed graph that rejects unknown
edge endpoints. None of these bypasses existing alignment or coverage.

## 4. B5.1 results

| System | R@1 | R@5 | R@10 | MRR | nDCG@10 | CER |
|---|---:|---:|---:|---:|---:|---:|
| Current Dense | 0.0400 | 0.0900 | 0.1117 | 0.1070 | 0.0863 | 0.0400 |
| Current Hybrid | 0.0950 | 0.1417 | 0.1900 | 0.1969 | 0.1593 | 0.1000 |
| Qwen3 Dense | N/A | N/A | N/A | N/A | N/A | N/A |
| Hybrid + Qwen3 | N/A | N/A | N/A | N/A | N/A | N/A |

These current-baseline results are a fresh B5 run, not a replacement for
historical P0-D numbers.

## 5. Model acquisition blocker

The local Qwen snapshot at revision
`97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` contained tokenizer/config files
but no `model.safetensors`. A direct revision-pinned Hugging Face download
attempt entered the `hf_xet` path and displayed an expected size of about
1.19 GB, but remained at 0 bytes after 118 seconds; it was interrupted. A
local-only Transformers load consequently returned `N/A` with an auditable
error. Full evidence is in `data/b5_model_attempts.json` and the run's
`model_manifest.json`.

## 6. Cost and failure analysis

Current dense query latency was P50/P95 `13.29/15.87 ms`; current hybrid was
`58.78/105.69 ms`. Qwen index/query latency is `N/A`. No GPU or money cost is
claimed. The only observed B5 failure is model acquisition/runtime blocking;
neural quality, hard-negative, visual, controller, and graph failure classes
remain unmeasured.

## 7. Decisions

- Current Dense: `KEEP_AS_OPTIONAL` as a reproducible CPU baseline.
- Current Hybrid: `KEEP_AS_OPTIONAL` as the stronger measured baseline in this
  run.
- Qwen3 Embedding: `INCONCLUSIVE`; not executed.
- Neural reranker, ColBERT, ColQwen, and graph-backed retrieval:
  `INCONCLUSIVE`; no real stage result exists.
- Typed controller and graph: `KEEP_AS_OPTIONAL` as contracts/primitives;
  end-to-end promotion is not justified.

## 8. Limitations

This report does not establish that Qwen3, a reranker, late interaction,
ColQwen, GraphRAG, or Agentic Search improves FinEvidence. It also does not
close the separate FinRAGBench-V public archive blocker or P0-J human
verification blocker. B5 remains partial until a real model path executes and
the frozen ablation is completed.
