# B3.2 — Benchmark Integrity & Public Closure

Date: 2026-09-14  
Status: `B3 = PARTIAL`

## 1. Research question

B3.2 asks whether the B3 visual result is an artifact of how `HSBCVisualStress-v1` was constructed, and whether the same retrieval pipeline behaves on a performance-blind natural HSBC control set. It also attempts to close the frozen 100-query `FinRAGBench-V-Slice-v1` page-image evaluation.

Historical B3.1 runs and metrics were not rewritten. The formal B3.2 experiment used code commit `622381ced70447c2539f81004da77f64809d3adf`, the existing CPU CLIP RN50 weights, the existing HSBC render/evidence manifests, and an isolated visual candidate pool per dataset.

## 2. Environment and provenance

- Runtime: Windows 11, Python 3.12.10, PyTorch `2.8.0+cpu`, CUDA unavailable.
- Visual model: `openai-clip-RN50`, `openai-public-RN50`, CPU; weights SHA-256 `f410876a343583bfc8b66cf22fe4cf228447c424b9a862c135d7f0d2b1b49998`.
- HSBC evidence: 492 parsed page records / 984 text+image Evidence objects.
- Render manifest: 494 pages at 72 DPI; SHA-256 `58e3b8ea105fdc808b52256702069b9a04529174234f7647fb382f577a21246e`.
- HSBC PDFs remain ignored local artifacts. The public source PDFs are not committed.

Formal runs:

| Run | Code commit | Metrics SHA-256 | Prediction SHA-256 (T0) |
|---|---|---|---|
| `artifacts/b3_2_runs/20260913T235754` | `622381c` | `D3BB64AA93993EC55EC82246FF8E1FA0178DA772A7E3C45E0978AA3E3F0C9B19` | `C768D32E4F9BFE80C7E2C7FADF8F970E85DDEAD4E30B8C15C0402B8BC0A70D2A` |
| `artifacts/b3_2_runs/20260914T000026` | `622381c` | `D3BB64AA93993EC55EC82246FF8E1FA0178DA772A7E3C45E0978AA3E3F0C9B19` | `C768D32E4F9BFE80C7E2C7FADF8F970E85DDEAD4E30B8C15C0402B8BC0A70D2A` |

Timing is not expected to be byte-identical on this CPU. The retrieval, ranking, and metric artifacts were byte-identical.

## 3. VisualStress construction audit

`HSBCVisualStress-v1` remains 60 cases: ten categories, six cases each. The audit selection was frozen before ranking inspection as the first two cases in original case order within each category. Its 20 IDs and source hash are in `benchmarks/hsbc_visual_stress_v1/audit_selection.json`; source cases SHA-256 is `70d8c8015acebfeb34f12950e2b69d6a5a9b35d552aa107aec52d271cc820a72`.

The audit found a real construction bias. All 60 questions are generated from only ten fixed templates, and every positive page was selected because a category keyword appeared in its parsed text. The positive is therefore a keyword-selected page, not an independently authored financial question with a naturally occurring evidence set. Only ten unique questions are repeated across the 60 cases. The audit did not use T0 or V0 results to select its sample.

The result explains, but does not by itself causally prove, the low T0 score:

| T0 page recall | Result |
|---|---:|
| @1 | 0/60 = 0.0000 |
| @5 | 0/60 = 0.0000 |
| @10 | 0/60 = 0.0000 |
| @50 | 7/60 = 0.1167 |

Thus `T0 Recall@10 = 0/60` is a reproducible observed ranking fact under the frozen stress workload, not a cutoff bug. It should not be presented as an unbiased estimate of natural text retrieval quality. The template asks for a page about broad keyword bundles such as `CET1 ratio capital`, while the positive page was selected by substring occurrence and may contain the relevant information in a table, layout, footnote, chart, or page-local context. This creates a text-failure-heavy stress workload by construction.

### Fixed 20-case attribution

The per-case audit is in `artifacts/b3_2_runs/visualstress_audit/fixed_sample.jsonl`; the all-60 audit is in `all_cases.jsonl`. Every row contains question, gold page, source block/hash, T0 candidates at @1/@5/@10/@50, lexical/entity/metric/period overlap, mapping status, and query-builder provenance.

| Primary attribution | Cases | Share |
|---|---:|---:|
| `TABLE_STRUCTURE_LOSS` | 8 | 40% |
| `CHART_VISUAL_ONLY` | 8 | 40% |
| `PAGE_FRAGMENTATION` | 2 | 10% |
| `LAYOUT_DEPENDENCY` | 2 | 10% |

No fixed-sample case was classified as `GOLD_MAPPING_ERROR`; all positive text pages and render pages existed. No case was labeled `OCR_CORRUPTION` or generic `TEXT_RETRIEVAL_MISS` by the deterministic primary classifier. That is not evidence that OCR or text retrieval are never causal; it means this fixed audit's category/source evidence supported the four listed explanations. Attribution is explicitly `deterministic_audit_inference`, not human causal adjudication.

Conclusion: the stress set is useful as a deliberately adversarial stress workload, but it is construction-biased and cannot support the claim that vision wins on ordinary financial questions.

## 4. HSBCNaturalMultimodal-v1

The natural control set contains 80 cases: 40 pages from the FY2025 Annual Report and 40 pages from the FY2025 Pillar 3 document. Selection was made by SHA-256 ordering of eligible corpus pages per document, before any T0/V0 evaluation. VisualStress candidate pages were excluded using the frozen stress manifest, not performance. Each case has one real positive page, adjacent real-page candidates, source content hashes, image hashes, and a query seed derived from the positive page's first heading-like line.

This is a project-created natural corpus control, not an official HSBC benchmark and not human-verified. Its selection manifest records `selection_frozen_before_retrieval=true`, `performance_blind=true`, source hashes, and the exclusion rule. The dataset is independent at page level from VisualStress positives/candidates and is reported separately.

## 5. Stress results

All numbers are page-level retrieval metrics over 60 stress cases. T1 is `Parsed Page Text`; verified Structured Table IR remains `N/A`.

| System | R@1 | R@5 | R@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| T0 Text Only | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| T1 Parsed Page Text | 0.0000 | 0.0000 | 0.0333 | 0.0044 | 0.0108 |
| V0 Visual Only | 0.0167 | 0.0500 | 0.1000 | 0.0303 | 0.0459 |
| M0 Fusion RRF | 0.0167 | 0.0167 | 0.0500 | 0.0209 | 0.0272 |
| M0 Fusion Weighted | 0.0167 | 0.0167 | 0.0500 | 0.0200 | 0.0263 |
| M1 Conditional Multimodal | 0.0167 | 0.0167 | 0.0500 | 0.0209 | 0.0272 |

At @10, M1 recovers 3 of 60 text failures (5.00%), with zero measured regressions and net recovery of 3 cases. This is a stress-set result only and is not a general visual advantage claim.

## 6. Natural-control results

| System | R@1 | R@5 | R@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| T0 Text Only | 0.1625 | 0.4250 | 0.5375 | 0.2840 | 0.3445 |
| T1 Parsed Page Text | 0.1625 | 0.4750 | 0.5875 | 0.3047 | 0.3729 |
| V0 Visual Only | 0.0000 | 0.0500 | 0.0750 | 0.0189 | 0.0320 |
| M0 Fusion RRF | 0.1625 | 0.3500 | 0.4500 | 0.2254 | 0.2775 |
| M0 Fusion Weighted | 0.1375 | 0.3500 | 0.4625 | 0.2173 | 0.2752 |
| M1 Conditional Multimodal | 0.1625 | 0.4375 | 0.5625 | 0.2877 | 0.3530 |

The natural control reverses the apparent story: text and parsed-page retrieval are materially stronger, while CLIP visual retrieval is weak. This is consistent with the control's text-derived query seeds and is precisely why the two workloads must not be pooled. It also shows that the control is not a claim about fully natural human questions; query construction remains a limitation.

## 7. Recovery and routing

The B3.2 runner retains explicit recovery cutoffs. Stress recovery is measured at the same K in numerator and denominator:

| K | Text failures | Recovery rate | Critical recovery | Regression | Net |
|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 1.67% | 1.67% | 0.00% | +1 |
| 5 | 60 | 1.67% | 1.67% | 0.00% | +1 |
| 10 | 60 | 5.00% | 5.00% | 0.00% | +3 |

The existing 30-case routing track remains unchanged and separate: visual invocation `23/30=76.67%`, unnecessary invocation `13/20=65.00%`, routing precision `43.48%`, recall `100%`, critical recovery `11.76%` over text-critical failures, regression `0%` at @10, net recovery `+2`. Because the offline runner computes V0 for an apples-to-apples baseline, invocation rate is a routing decision statistic, not proof of an end-to-end production cost saving.

## 8. FinRAGBench-V public closure

The slice remains frozen:

- dataset: `zhaosuifeng/FinRAGBench-V`
- revision: `d0d65255c94e687caa81ac9da7758ed25ff046a5`
- slice: `FinRAGBench-V-Slice-v1`, 100 queries
- query/qrel hashes unchanged

The Windows `huggingface_hub`/`hf_xet` attempt remains in `data/finragbench_v_source/download_blocker.json`. B3.2 added a WSL Ubuntu attempt using `wget -c` against the official revision-pinned resolve URL. The official response returned `X-Repo-Commit` equal to the frozen revision, `HTTP 200`, `Accept-Ranges: bytes`, and expected archive length 2,378,037,659 bytes. The observed transfer rate projected over two hours; the bounded attempt was stopped at 10,037,760 bytes. Full headers/progress are retained in `data/finragbench_v_source/wsl_wget_attempt.log`, with a structured summary in `b3_2_download_blocker.json`.

The partial file is not treated as an archive, no PDFs were extracted from it, and no public page-image metrics were run. Therefore T0/T1/V0/M0/M1 on FinRAGBench-V remain `N/A`. This is an external transport blocker, not a benchmark result.

## 9. Latency

The first formal run's CPU timing is the recorded reference; the second run is the reproducibility check. Offline indexing is not mixed into query latency.

| Component | P50 ms | P95 ms |
|---|---:|---:|
| Text retrieval | 186.46 | 402.31 |
| Parsed-page retrieval | 186.30 | 429.21 |
| Visual query encoding/retrieval | 95.88 | 333.74 |
| Fusion | 0.10 | 0.17 |
| Routing | 0.03 | 0.05 |
| Evidence qualification | 5.91 | 10.48 |
| End-to-end | 496.69 | 1,285.58 |

Offline indexing: text 22,666 ms, parsed-page 22,786 ms, visual 61,051 ms for 309 candidate images (81 legacy stress/routing pages plus 228 natural-control pages). This is CPU-only timing; no GPU or monetary cost claim is made.

## 10. What actually needs vision?

Supported by this audit and the existing stress categories:

- Chart value/legend, visual-only content, and page layout relations are the strongest candidates for vision. Text-only extraction cannot encode a curve-to-label or spatial relation reliably.
- Table row/column, multi-level header, and unit problems are not automatically “vision problems.” They more directly require structure-preserving table IR, header/unit association, or a parser/OCR repair path. Vision may help as a fallback, but this run did not prove it.
- Footnote/page-fragmentation and weak text ranking should first receive page-aware text retry, query rewrite, adjacent-page expansion, or structured evidence qualification. Visual invocation is not justified merely because T0 missed.

The measured natural-control result rejects an always-visual policy. Conditional routing can be evaluated as a selective policy, but the current stress/routing workload does not establish production cost savings: the offline evaluator still computes visual baselines for comparison, and the observed router invoked vision unnecessarily on 65% of non-visual routing cases.

## 11. Scientific limits and rejected claims

Supported claims:

1. `T0 Recall@10=0/60` is reproducible on the frozen VisualStress workload and becomes `7/60` at @50.
2. VisualStress construction is biased toward keyword-selected, template-generated text failures.
3. A performance-blind 80-case real-page HSBC control can be built and yields materially different results.
4. In this corpus and CPU CLIP setup, text/parsed-page retrieval is stronger than visual-only retrieval on the control set.
5. B3.2 cannot close the public FinRAGBench-V page-image evaluation without the verified archive.

Rejected claims:

- Vision generally beats text RAG on financial documents.
- VisualStress is an unbiased natural benchmark.
- Current conditional routing has demonstrated production cost savings.
- T1 is a verified structured table IR.
- Page hits are bbox/region grounding; bbox gold is unavailable, so bbox metrics are `N/A`.

## 12. B3 decision and B4 recommendation

`B3 = PARTIAL`, not `COMPLETE`, because the frozen public page-image evaluation was not completed. The HSBC integrity audit, independent control set, corrected cutoff interpretation, and two reproducibility runs are complete.

Do not enter B4 production hardening yet. The next justified gate is public archive acquisition and evaluation closure, followed by a separately designed human-authored or human-verified multimodal question set if the project needs claims beyond these corpus-derived controls.
