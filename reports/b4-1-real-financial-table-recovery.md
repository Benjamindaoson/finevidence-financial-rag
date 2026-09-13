# B4.1 — Real Financial Table Recovery & Executable Structured Retrieval

Date: 2026-09-14  
Status: **COMPLETE for the scoped HSBC table-recovery experiment**  
Code commit: `16137e652215edc83f01d044f5826e9787a7c15e`

## 1. Research question

Can a real PDF-to-TableIR executor recover enough table structure from the existing HSBC Annual Report to improve retrieval on the frozen table-failure slice, while still passing candidates through FinEvidence evidence qualification?

This phase does not reopen B3, does not claim verified semantic cell accuracy, and does not turn the deterministic executor into a neural reranker.

## 2. Data and provenance

The experiment uses the frozen `HSBCVisualStress-v1` set: 60 cases, of which 24 are in the table-focused categories `TABLE_ROW_MIXING`, `TABLE_COLUMN_MIXING`, `MULTI_LEVEL_HEADER`, and `UNIT_HEADER_LOSS`. The source PDF is the existing public HSBC FY2025 Annual Report artifact:

- local artifact: `artifacts/hsbc_local_sources/01-hsbc-fy2025-annual-report.pdf`
- document id used by the evidence manifest: `hsbc-fy2025-annual-report`
- extraction scope: PDF pages 1–26 (the pages containing the frozen table slice plus nearby real distractor tables)
- source SHA256: recorded in each run's `dataset_manifest.json`
- formal runs: `artifacts/b4_1_runs/20260914T013358/` and `artifacts/b4_1_runs/20260914T013551/`

No PDF is committed. The run directories are ignored local artifacts.

## 3. E0 — Real PDF structure recovery

`pdfplumber` positioned words and table-like regions are converted into TableIR. Numeric columns use x-position clustering and rows use y-position grouping; the resulting cells retain table, row, column, page, and optional cell bounding-box provenance.

| Field | Result | Interpretation |
|---|---:|---|
| Parsed table regions | 24 | Real regions accepted by the bounded extractor |
| Pages with accepted regions | 13 | Within the 26-page scope |
| Table parse success | 1.0000 | Parser produced a TableIR for every accepted region; not semantic correctness |
| Structure recoverable rate | 0.7418 | Fraction of emitted TableIR cells with a recovered bbox |
| Cell identity preservation | 1.0000 | TableIR identity invariant |
| Row/column relation | 1.0000 | TableIR relation invariant |
| Header path population | 0.7278 | Header text was attached to this fraction of cells |
| Unit association accuracy | N/A | No verified human cell/unit gold |
| Merged-cell accuracy | N/A | No verified human gold |
| Semantic cell accuracy | N/A | No verified human gold |

The important limitation is visible in the extractor itself: real financial PDFs often expose geometry without an explicit semantic grid. The invariants prove that the internal representation is addressable, not that every recovered cell means exactly what a human reader intends.

## 4. Systems and qualification contract

- **T0 Text Only**: frozen generic hybrid retrieval over page text (`alpha=0.70`).
- **T1 Parsed Page Text**: frozen parsed-page-text comparator (`alpha=0.45`). It is not Verified Structured Table IR.
- **T2 Real Structured Table IR**: deterministic TableIR cell executor. Cell evidence includes row label, header context, value, unit/period when present, table id, row id, column id, and bbox.
- **V0 Visual Only**: the existing real CPU CLIP RN50 page-image retriever.
- **T2 + Text**: RRF over T1 and T2 ranks.
- **Oracle Table Executor**: diagnostic route that selects T2 for the four frozen table categories; it is not a deployable router.

Every T2 result is an `Evidence(modality="table")` object and is passed through `align_requirement_to_evidence` and `evaluate_independent_coverage`. A table cell is accepted by the page-level gold bridge only if it is on the gold page and passes lexical alignment; page membership alone cannot make it eligible.

## 5. Retrieval results — all 60 frozen stress cases

| System | R@1 | R@5 | R@10 | MRR | nDCG@10 | Independent critical coverage | Eligible rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| T0 Text Only | 0.0000 | 0.0000 | 0.0000 | 0.0030 | 0.0000 | 0.0000 | 0.0000 |
| T1 Parsed Page Text | 0.0000 | 0.0000 | 0.0333 | 0.0088 | 0.0108 | 0.0333 | 0.0333 |
| T2 Real Structured Table IR | 0.0167 | 0.0833 | 0.0833 | 0.0381 | 0.0491 | 0.0667 | 0.0667 |
| V0 Visual Only | 0.0167 | 0.0500 | 0.1000 | 0.0469 | 0.0459 | 0.1000 | 0.1000 |
| T2 + Text | 0.0167 | 0.0333 | 0.0833 | 0.0305 | 0.0396 | 0.0500 | 0.0500 |
| Oracle Table Executor | 0.0167 | 0.0833 | 0.0833 | 0.0405 | 0.0491 | 0.0667 | 0.0667 |

The T2 gain is real but small on this frozen workload: it recovers five of 24 table-category page misses by cutoff 10 relative to T1, and four of 24 critical qualification failures. It does not establish that the recovered cells are semantically correct, because the slice has page-level evidence gold rather than verified cell-level gold.

## 6. Table-failure recovery

All recovery values below use the T1 comparator and are reported at explicit cutoffs.

| Cutoff | T2 page recovered | T2 recovery rate | T2 critical recovered | T2 critical recovery rate | T2 regression | Net recovery |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0.0417 | 1 | 0.0417 | 0 | +1 |
| 5 | 5 | 0.2083 | 3 | 0.1250 | 0 | +5 |
| 10 | 5 | 0.2083 | 4 | 0.1667 | 0 | +5 |

T2+Text is weaker than T2 at cutoff 5 (2 recovered cases) and reaches 4 recovered cases at cutoff 10. RRF therefore did not provide a free improvement on this workload. V0 remains the strongest page-recall baseline at cutoff 10, while T2 has the strongest result among structured/table systems.

## 7. Failure analysis

The frozen questions are intentionally generic page-location probes, not verified cell-value questions. That is why a geometry-aware executor cannot be credited with semantic table recovery simply from a page hit. The observed failure pattern is:

- pages 1–13 of the table-category subset contain no accepted table region in the extraction scope, so T2 cannot recover those cases;
- the generic query language (`segment geography business`, `USD million bn basis points`) is only weakly aligned with the recovered table cells;
- multiple cells from the same table can crowd the top-k cell list, so page recall is sensitive to cell-to-page aggregation;
- T2 recovered qualified evidence on cases `hsbc-v-0015`, `hsbc-v-0018`, `hsbc-v-0020`, and `hsbc-v-0024`; the fifth page-level recovery did not produce a qualified critical answer under the stricter alignment gate;
- no regression against T1 was observed at the table-category cutoffs in this run.

Cell-level wrong-row, wrong-column, merged-header, and unit-confusion rates are **N/A**, not zero: no human-verified TableIR gold exists.

## 8. Latency and cost proxy

Measured on CPU with the existing CLIP RN50 visual adapter. Offline parsing and visual indexing are separate from query latency.

| Component | P50 run 1 (ms) | P95 run 1 (ms) | P50 run 2 (ms) | P95 run 2 (ms) |
|---|---:|---:|---:|---:|
| Text retrieval | 149.94 | 216.63 | 190.33 | 245.32 |
| Parsed page retrieval | 146.09 | 219.85 | 200.50 | 425.62 |
| Structured TableIR retrieval | 11.27 | 20.85 | 16.42 | 27.12 |
| Visual retrieval | 93.68 | 151.05 | 93.07 | 238.74 |
| T2+Text fusion | 149.65 | 218.04 | 198.28 | 261.33 |
| Routing | 0.02 | 0.04 | 0.03 | 0.05 |
| Evidence qualification | 3.66 | 7.21 | 4.38 | 8.76 |
| End-to-end | 582.14 | 842.99 | 763.33 | 1121.44 |

Offline costs were 7,097.68 ms and 5,343.54 ms for PDF table extraction over 26 pages; visual indexing of 78 pages was 6,708.80 ms and 11,362.73 ms. These are machine-load-sensitive timing observations, not a production cost estimate.

## 9. Reproducibility

Runs `20260914T013358` and `20260914T013551` used the same code commit, configuration, PDF SHA256, evidence/render manifest hashes, page scope, and model manifest. The following structural/ranking outputs were byte-identical: `config.json`, `dataset_manifest.json`, `metrics.json`, `structure_fidelity.json`, `table_ir.jsonl`, all system prediction JSONL files, and `failure_cases.jsonl`. Timing metrics varied with CPU load and are reported separately.

## 10. Claims supported

- A real public HSBC PDF can be converted into addressable TableIR cells with stable row/column identity and partial geometry recovery.
- A deterministic TableIR executor can recover a small number of page/critical-evidence failures on the frozen table slice.
- T2 is materially different from T1 Parsed Page Text and is cheap at query time once indexed.
- Existing Evidence Qualification can gate structured candidates instead of treating table retrieval as sufficient.

## 11. Claims rejected or still unproven

- `Table Parse Success = 1` does not mean semantic table accuracy is 1.
- This experiment does not prove that T2 solves merged cells, cross-page tables, or unit association.
- T2 does not beat V0 on page recall@10 in this workload.
- T2+Text is not better than T2 here; fusion is not automatically beneficial.
- The diagnostic Oracle route is not evidence that predicted routing improves quality.
- No production-scale throughput, GPU serving cost, or human-level table correctness has been established.

## 12. B3/B4.1 status

`B4.1 = COMPLETE` for the scoped real-HSBC table-recovery and structured-retrieval experiment. B3 remains `PARTIAL` because the independent FinRAGBench-V public corpus/page-image closure is still an external blocked track; B4.1 does not change that historical status.

The next justified step is a small, explicitly human-verified table-structure subset if semantic cell accuracy is needed. Full production hardening is not justified by this experiment alone.
