# B3 — Multimodal Evidence Retrieval & Visual Grounding (pre-B3.1 historical record)

Status: `PARTIAL` (superseded by `reports/b3-1-public-benchmark-evaluation-closure.md`)

This file records the first B3 run before the B3.1 evaluation closure. Current names, recovery cutoffs, mixed routing results, and component latency are in the B3.1 report; do not use the historical unlabelled recovery statements below as the current metric contract.

The executable HSBC visual track is complete. The public FinRAGBench-V page-image track is not complete because its required 2.378GB `pdf_en.tar.gz` archive timed out from Hugging Face after three retries. Queries and qrels are fixed as `FinRAGBench-V-Slice-v1`; no page-image score is claimed for that slice.

## 1. Research question

Which critical financial evidence failures actually require vision, and can those failures be recovered without paying multimodal inference cost on every query?

## 2. Environment and model provenance

- Windows 11, Python 3.12.10, PyTorch 2.8.0, Transformers 4.55.4.
- CUDA: unavailable; GPU memory is therefore `0 MB` and no GPU-seconds claim is made.
- CPU-only visual model: OpenAI CLIP RN50 through `openai-clip==1.0.1`.
- Model weights: 244MB, manifest hash `f410876a343583bfc8b66cf22fe4cf228447c424b9a862c135d7f0d2b1b49998`.
- Visual retrieval reads rendered PNG image paths through `encode_images`; it is not OCR-text embedding renamed as visual retrieval.
- Exact formal experiment code commit: `7589c57`.

## 3. Data

### HSBC corpus

The corpus is the official FY2025 HSBC Annual Report and FY2025 Pillar 3 Disclosure. The tracked provenance is `data/hsbc_corpus_manifest.json`; the two PDFs remain ignored local artifacts.

| Document | Pages | SHA-256 |
|---|---:|---|
| FY2025 Annual Report | 372 | `94aab2f5c83d1060ee95d344f1915833869fe4502dc635e4ab9ca84f496ee94b` |
| FY2025 Pillar 3 | 122 | `eb64c8f0fcd32648512979886bceddba7128558761c07948b50f6ecfa83a32f7` |

### Rendering

`scripts/render_pdf_pages.py` uses Poppler `pdftoppm` at fixed 72 DPI and emits 494 PNG pages. `artifacts/hsbc_page_images/page_render_manifest.json` records document, page, image path, image SHA-256, dimensions, DPI, renderer version, and source PDF hash. Re-rendering checks existing image bytes and records the same hash.

### HSBCVisualStress-v1

60 cases were mined from actual parsed HSBC page blocks and rendered pages: 10 categories × 6 cases — table row/column mixing, multi-level header, unit/header loss, footnote loss, chart value/legend, caption mismatch, multi-column order, and visual-only information. Every candidate points to an actual document/page/image; no page or candidate text was fabricated. The set is project-created, model-assisted adjudicated, and `human_verified=false`.

### FinRAGBench-V-Slice-v1

100 English queries were fixed from the public queries and qrels files. The required PDF archive could not be retrieved in this run (`UNAVAILABLE_HF_ARCHIVE_TIMEOUT`), so page retrieval, citation, and visual scores are `N/A` rather than inferred from metadata.

## 4. Retrieval systems

- `T0 Text Only`: HybridRetriever over pypdf page text.
- `T1 Parsed Page Text`: the existing lexical/dense page-text adapter with a separate configuration; verified structured Table IR remains `N/A`.
- `V0 Visual Only`: CLIP text-to-image ranking over candidate page images.
- `M0 Fusion RRF`: rank-based fusion.
- `M0 Fusion Weighted`: min-max-normalized modality scores followed by weighted fusion.
- `M1 Conditional Multimodal`: coverage-aware route; unresolved critical coverage triggers visual retrieval, otherwise text/table route is retained.

All final candidates continue through `FactEvidenceAlignment` and `evaluate_independent_coverage`. A visual page hit alone is not a qualified requirement. Bbox metrics are `N/A` because this stress set has no verified bbox gold.

## 5. Retrieval results

Final run results on 60 HSBCVisualStress-v1 cases:

| System | Page R@1 | Page R@5 | Page R@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| T0 Text Only | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| T1 Parsed Page Text | 0.0000 | 0.0000 | 0.0333 | 0.0044 | 0.0108 |
| V0 Visual Only | 0.0167 | 0.0500 | 0.1000 | 0.0303 | 0.0459 |
| M0 Fusion RRF | 0.0167 | 0.0167 | 0.0500 | 0.0209 | 0.0272 |
| M0 Fusion Weighted | 0.0167 | 0.0167 | 0.0500 | 0.0200 | 0.0263 |
| M1 Conditional Multimodal | 0.0167 | 0.0167 | 0.0500 | 0.0209 | 0.0272 |

The low absolute recall is retained. This stress construction intentionally asks for page-level evidence from a long two-document corpus; it is not a leaderboard score and does not prove that CLIP is a suitable production financial retriever.

## 6. B3 recovery and regression

| Metric | Result |
|---|---:|
| Text Failure Recovery@10 | 0.0500 (3/60 text failures recovered by M1) |
| Visual Critical Requirement Recovery@10 | 0.0500 |
| Multimodal Regression@10 | 0.0000 |
| Net Recovery@10 | +3 cases |
| Visual routing precision | 0.5000 |
| Visual routing recall | 1.0000 |
| Visual invocation rate | 1.0000 |
| Unnecessary invocation rate | 1.0000 |
| Visual pages/query | 10.0 |

The invocation result is an important negative finding: every case initially lacked the qualified critical requirement under this stress construction, so the conditional router could not save calls. This demonstrates the instrumentation, not a cost win. A broader mixed workload containing genuinely text-sufficient questions is required before claiming cost reduction.

## 7. Citation and grounding

Page precision/recall/F1 are computed per query in `grounding_predictions.jsonl`; aggregate page F1 is equivalent to page hit on this one-positive-page design. Bbox IoU and region precision/recall are `N/A: no bbox gold in HSBCVisualStress-v1`. Page hit is not reported as bbox grounding.

For M1 top-5 citations, macro page precision/recall/F1 are `0.0033 / 0.0167 / 0.0056`. These values are intentionally low and consistent with the stress-set retrieval result.

## 8. Structure fidelity

The regression probe exists in `src/finevidence/eval/structure.py`. On the current pypdf page parser, cell alignment, multi-level header relations, footnote edges, cross-page continuity, and multi-column reading order are explicitly `N/A`; the system does not claim that page text preserved them. The executable result therefore supports only this limited conclusion: page images are available for a second retrieval channel, while the current structured IR is not yet a verified table-structure representation.

## 9. Per-failure-type results

Per-category Page Recall@5 is emitted in `per_failure_type_metrics.json`. The only recovered categories in this run were:

- `FOOTNOTE_LOSS`: V0 0.1667; other headline systems 0.0000.
- `MULTI_LEVEL_HEADER`: V0 0.1667; other headline systems 0.0000.
- `VISUAL_ONLY_INFORMATION`: V0/M0/M1 0.1667; T0/T1 0.0000.
- All remaining categories: 0.0000 at Page Recall@5 for the headline systems.

This is evidence that the current CLIP baseline contributes on a small visual/layout slice, not evidence that vision solves financial table retrieval generally.

## 10. Latency and cost proxy

CPU P50/P95 query latency in the final run:

| System | P50 ms | P95 ms |
|---|---:|---:|
| T0 Text Only | 210.5 | 237.5 |
| T1 Parsed Page Text | 211.9 | 246.1 |
| V0 Visual Only | 73.1 | 86.2 |

Fusion and routing composition time was not separately instrumented in this pre-B3.1 historical run and is therefore `N/A`, not zero. See the B3.1 report for the corrected component-level latency run. Model indexing time is excluded from query latency. GPU memory/seconds are `N/A` on a CUDA-free host; `peak_gpu_memory_mb=0.0` records the observed CPU path.

## 11. Representative badcases

- Text failed → visual recovered: the recovery rows are in `failure_cases.jsonl` with `visual_recovered=true`; three cases were recovered by M1.
- Text correct → visual regression: zero cases in this run. This is a result, not an omitted section.
- Structured parsing solved it → visual unnecessary: no such case is proven because the current T1 adapter is not a verified structured-table parser.
- Text and visual both failed: the majority of the 60 cases; examples and full traces are retained rather than cherry-picked.

## 12. Reproducibility

Formal runs:

- `artifacts/b3_runs/20260913T114012`
- `artifacts/b3_runs/20260913T114144`

Both use commit `7589c57`, the same manifests, render configuration, CLIP weight hash, and seed. All formal metrics, rankings, failure rows, routing outputs, and grounding outputs were byte-identical. Query traces were structurally identical after excluding expected CPU timing variation; maximum summed text+visual latency delta was 281.6694 ms.

## 13. Supported and rejected claims

Supported:

- A real image encoder can be integrated into the existing Evidence IR without sacrificing page provenance.
- On these HSBC stress cases, CLIP visual retrieval recovered 3 text failures through the conditional path and introduced no measured regression.
- Page citation can be evaluated separately from bbox grounding, and missing bbox gold remains `N/A`.
- A coverage-triggered visual route is observable; in this workload it invoked vision for 100% of queries and did not demonstrate a cost reduction.

Rejected:

- This is not evidence that CLIP RN50 is production-grade for financial chart/table retrieval.
- This is not evidence that multimodal fusion beats text or a real structured-table IR.
- No bbox or region grounding claim is made.
- No FinRAGBench-V page-image score is claimed.
- No GPU scalability or monetary cost claim is made.

## 14. B3 decision and limits

`B3 = PARTIAL`. The real visual model, deterministic page rendering, HSBC visual stress evaluation, five baseline paths, evidence qualification, recovery/regression metrics, latency instrumentation, and two reproducibility runs are present. The blocker is the unavailable FinRAGBench-V PDF archive, so the required public multimodal benchmark evaluation is not complete. Additional limits are the CPU-only model, page-level rather than region-level gold, a pypdf parser without verified table geometry, model-assisted rather than human verification, and a stress workload that is too retrieval-hard to establish a production quality/cost tradeoff.

The next production-hardening step is not unconditional VLM serving. It is first fixing the public benchmark slice and adding a verified structured-table IR plus a mixed text-sufficient workload; only then can the visual recovery/cost decision be trusted.
