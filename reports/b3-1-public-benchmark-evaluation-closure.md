# B3.1 — Public Benchmark & Evaluation Closure

Status: `PARTIAL`

B3.1 closed the HSBC evaluation and measurement gaps, but the public FinRAGBench-V page-image slice remains blocked by Hugging Face/Xet transport. Therefore this phase does not claim a public multimodal benchmark score and does not promote B3 to `COMPLETE`.

## 1. What was tested

The narrow question was whether the existing B3 evidence-qualified visual path could be evaluated with unambiguous recovery cutoffs and a genuinely mixed routing workload, while fixing the frozen public benchmark provenance. No P0-H rerun, new visual architecture, VLM serving, or production hardening was introduced.

## 2. Public FinRAGBench-V closure

`FinRAGBench-V-Slice-v1` remains a fixed 100-query metadata/qrels slice. The query and qrels hashes are unchanged:

- `queries_en.json`: `e748958ed09450066cd06cf8dc5ee324c8c66380e3169f235e3f66faaa5277c6`
- `qrels_en.tsv`: `dd3e5085dcf74339ba511d7b8844a4e9c0d3e3655b6564a9f276f840263202c0`
- Dataset revision: `d0d65255c94e687caa81ac9da7758ed25ff046a5`
- Required file: `pdfs_for_QA/pdf_en.tar.gz`

The official `huggingface_hub.hf_hub_download` path was attempted with `huggingface_hub==0.34.4` and `hf_xet==1.6.0`, project-local cache directories, and the pinned revision. The first attempt exposed a missing inherited Xet log directory; after explicitly setting `HF_HOME`, `HF_HUB_CACHE`, and `HF_XET_CACHE`, the Xet transfer remained at a zero-byte incomplete object with no progress. A short official HTTP fallback also remained at zero bytes. The incomplete object/lock and traceback are retained in `data/finragbench_v_source/download_blocker.json` and `data/finragbench_v_source/download_blocker_notes.md`.

Consequently, page-image evaluation for FinRAGBench-V-Slice-v1 is `N/A` for T0, T1, V0, M0, and M1. No metadata hit is presented as a page-image result, and no archive was extracted.

## 3. HSBC data and rendering

The executable real-data track remains the official HSBC FY2025 Annual Report (372 pages, SHA-256 `94aab2f5c83d1060ee95d344f1915833869fe4502dc635e4ab9ca84f496ee94b`) and FY2025 Pillar 3 Disclosure (122 pages, SHA-256 `eb64c8f0fcd32648512979886bceddba7128558761c07948b50f6ecfa83a32f7`). Pages are rendered deterministically at 72 DPI; the existing render manifest records image hashes, dimensions, renderer version, and source PDF hashes.

`HSBCVisualStress-v1` is unchanged at 60 project-created cases. Candidates still point to real parsed blocks and page images, with `human_verified=false`.

`HSBCMultimodalRouting-v1` is a separate 30-case real-page routing workload, balanced as:

| Class | Cases |
|---|---:|
| `TEXT_SUFFICIENT` | 10 |
| `TABLE_PARSED_SUFFICIENT` | 10 |
| `VISUAL_NEEDED` | 10 |

The route label is metric-only. The router receives question text, parser confidence, and observed qualification coverage; it never receives the gold modality label.

## 4. Baseline naming and structure boundary

The five paths remain comparable, but T1 is now honestly named `T1 Parsed Page Text`. It is a separate configuration of the existing page-text retriever, not a verified structured-table IR. Cell identity, row/column relations, multi-level headers, unit edges, footnote edges, and table geometry remain `N/A`.

## 5. HSBCVisualStress-v1 page retrieval

The following are the final 60-case stress results from run `artifacts/b3_runs/20260913T132951` (the second reproducibility run has the same values):

| System | Page R@1 | Page R@5 | Page R@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| T0 Text Only | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| T1 Parsed Page Text | 0.0000 | 0.0000 | 0.0333 | 0.0044 | 0.0108 |
| V0 Visual Only | 0.0167 | 0.0500 | 0.1000 | 0.0303 | 0.0459 |
| M0 Fusion RRF | 0.0167 | 0.0167 | 0.0500 | 0.0209 | 0.0272 |
| M0 Fusion Weighted | 0.0167 | 0.0167 | 0.0500 | 0.0200 | 0.0263 |
| M1 Conditional Multimodal | 0.0167 | 0.0167 | 0.0500 | 0.0209 | 0.0272 |

The prior negative conclusions hold: CLIP absolute recall is low; fusion is not better than Visual Only on this stress workload; and no production visual-retriever claim follows.

## 6. Corrected recovery metrics

Recovery now has an explicit cutoff. The denominator is text failures at the same K, and regression is measured at the same K.

### HSBCVisualStress-v1, 60 cases

| Cutoff | Text failures | Text failure recovery | Visual critical requirement recovery | Regression | Net recovery |
|---:|---:|---:|---:|---:|---:|
| @1 | 60 | 1/60 = 0.0167 | 0.0167 | 0.0000 | +1 |
| @5 | 60 | 1/60 = 0.0167 | 0.0167 | 0.0000 | +1 |
| @10 | 60 | 3/60 = 0.0500 | 0.0500 | 0.0000 | +3 |

Thus the historical statement “3/60” is now explicitly `Text Failure Recovery@10`, not an unlabelled recovery statistic.

## 7. Mixed routing evaluation

On `HSBCMultimodalRouting-v1`:

| Metric | Result |
|---|---:|
| Routing precision | 10/23 = 0.4348 |
| Routing recall | 10/10 = 1.0000 |
| Visual invocation rate | 23/30 = 0.7667 |
| Unnecessary visual invocation rate | 13/20 = 0.6500 |
| Critical requirement recovery | 2/17 = 0.1176 |
| Multimodal regression | 0/30 = 0.0000 |
| Net recovery | +2 |

Route confusion was:

- `VISUAL_NEEDED`: 10/10 routed to `VISUAL`.
- `TABLE_PARSED_SUFFICIENT`: 1/10 routed to `TABLE`, 9/10 unnecessarily routed to `VISUAL`.
- `TEXT_SUFFICIENT`: 6/10 routed to `TEXT`, 4/10 routed to `VISUAL` because observed text qualification was incomplete.

The mixed set therefore demonstrates that conditional routing is measurable, but does not demonstrate cost saving: it still invokes visual retrieval for 76.7% of queries, with 65.0% unnecessary invocation among non-visual cases. This is a retained negative result, not a router success claim.

Recovery on the routing workload is cutoff-sensitive:

| Cutoff | Text failures | Recovery | Regression | Net |
|---:|---:|---:|---:|---:|
| @1 | 29 | 1/29 = 0.0345 | 1/30 = 0.0333 | 0 |
| @5 | 22 | 1/22 = 0.0455 | 3/30 = 0.1000 | -2 |
| @10 | 17 | 2/17 = 0.1176 | 0/30 = 0.0000 | +2 |

## 8. Latency and cost proxy

Query latency is separated from offline indexing. Run `20260913T132951` measured on CPU:

| Component | P50 ms | P95 ms |
|---|---:|---:|
| Text retrieval | 208.78 | 222.85 |
| Parsed-page retrieval | 208.22 | 222.21 |
| Visual query encoding/retrieval | 71.09 | 77.42 |
| Fusion | 0.12 | 0.14 |
| Routing | 0.03 | 0.05 |
| Evidence qualification | 6.22 | 7.61 |
| End-to-end | 502.07 | 528.96 |

Offline indexing is not mixed into query latency:

| Operation | Observed ms |
|---|---:|
| Text index | 15,559.86 |
| Parsed-page index | 18,165.35 |
| Visual image index | 6,535.76 |
| Visual pages indexed | 81 |

CUDA was unavailable. GPU memory, GPU seconds/query, and monetary cost are therefore not claimed. `visual_pages_per_query=10.0` is recorded as a workload proxy, not a price estimate.

## 9. Citation and structure fidelity

Page citation precision/recall/F1 continue to be computed against available page-level gold in `grounding_predictions.jsonl`. Bbox/region metrics remain `N/A`; neither HSBC set has verified bbox gold. Page hits are not bbox grounding.

Structure fidelity remains limited to the existing parser probe. Verified structured Table IR is `N/A`; T1 does not solve row/column, multi-level header, unit, footnote, cross-page continuity, caption association, or multi-column geometry.

## 10. Representative cases

- Text failed → visual recovered: `hsbc-v-0014` (`MULTI_LEVEL_HEADER`), `hsbc-v-0025` (`FOOTNOTE_LOSS`), and `hsbc-v-0057` (`VISUAL_ONLY_INFORMATION`) at the @10 recovery cutoff.
- Text correct → multimodal regression: none on the 60-case stress set at @10; the routing workload has regressions at @1 and @5, retained in its trace.
- Structured parsing solved it → visual unnecessary: the experiment cannot make this claim because T1 is not verified structured IR.
- Both text and visual failed: the majority of stress cases; complete traces and failure rows are retained without cherry-picking.

## 11. Reproducibility

Final pair:

- `artifacts/b3_runs/20260913T132951`
- `artifacts/b3_runs/20260913T133136`

Both use code commit `52554ea096fdd846cde7981f269a2c245b2a1732`, identical CLIP weight hash `f410876a343583bfc8b66cf22fe4cf228447c424b9a862c135d7f0d2b1b49998`, the same render and dataset manifests, and the same seed. Config, model, dataset, metrics, per-category metrics, failure rows, all rankings, routing, and grounding artifacts are byte-identical. CPU latency differs naturally; maximum delta over recorded timing fields was 650.4 ms, so only metric/ranking determinism is claimed.

## 12. B3.1 gate decision

| Gate | Result |
|---|---|
| Public FinRAGBench-V page-image evaluation | `NO — blocked by official archive transport` |
| HSBCVisualStress-v1 retained and evaluated | `YES` |
| HSBCMultimodalRouting-v1 completed | `YES` |
| Recovery cutoff ambiguity fixed | `YES — @1/@5/@10` |
| Component latency instrumentation | `YES` |
| Two final reproducibility runs | `YES` |

Final status: **`B3 = PARTIAL`**. The only B3.1 completion blocker is the unavailable pinned FinRAGBench-V PDF archive. No production hardening should begin under the current evidence boundary; the next valid step is to obtain the same pinned archive or an explicitly approved equivalent public page-image slice, then run the existing evaluator without changing its conclusions.

## 13. Supported claims

- The real CLIP model consumes rendered page images and preserves page-level provenance in the existing Evidence IR.
- The original 60-case HSBC stress track remains low-recall and reproducible.
- Visual retrieval recovers a small number of text failures at @10, with no stress-set regression at @10.
- Conditional routing can be measured on real mixed pages, but this workload does not prove multimodal cost savings.
- Recovery metrics are now unambiguous at @1, @5, and @10, and offline indexing is separated from query latency.

## 14. Rejected claims and limits

- No FinRAGBench-V page-image score is claimed.
- CLIP RN50 is not shown to be production-grade for financial charts/tables.
- Fusion is not shown to beat Visual Only or a verified structured-table IR.
- No bbox/region grounding claim is made.
- No GPU scale or monetary cost claim is made.
- HSBCMultimodalRouting-v1 is a project-created stress/evaluation set from public HSBC disclosures, not an HSBC-official benchmark; its labels are model-assisted and `human_verified=false`.
