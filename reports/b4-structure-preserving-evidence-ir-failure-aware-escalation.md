# B4 — Structure-Preserving Evidence IR & Failure-Aware Escalation

Date: 2026-09-14  
Status: **COMPLETE for the experimental B4 scope**  
Code commit: `8bee650`  
Historical boundary: P0-H, B3.1 and B3.2 were not re-run or rewritten. B3 remains `PARTIAL` because the frozen FinRAGBench-V page-image evaluation is still externally blocked.

## 1. Research question

When a critical requirement is missing, can the system distinguish a text retrieval miss from table-structure loss, page fragmentation, layout dependency, or visual-only evidence, and choose text retry, structured retrieval, adjacent-page retrieval, visual retrieval, or abstention accordingly?

The experiment deliberately separates:

- E0: an oracle failure route using the frozen gold failure category, for measuring recovery headroom only;
- E1: a performance-blind predicted route using only the question, observed initial coverage, and parser capability;
- qualification: every route still passes through the existing Evidence alignment and critical-coverage gate.

## 2. Structure-preserving Table IR

`TableIR` and `TableCell` were added in `src/finevidence/contracts/table.py` and `src/finevidence/evidence/table_ir.py`. Each cell retains a stable `cell_id`, `row_id`, `column_id`, source record/page, raw value, header path, inferred period/unit, and optional geometry. `TableIR` retains table identity, header rows, row/column IDs, caption/footnote slots, and source provenance.

The real TAT-QA source tables used by `RealFinance-v1` were parsed without modifying the frozen benchmark. There were 15 unique tables among the 50 selected TAT-QA questions. Results:

| Invariant | Result |
| --- | ---: |
| Parse success | 15/15 = 1.0000 |
| Raw value round-trip | 15/15 = 1.0000 |
| Cell identity uniqueness | 15/15 = 1.0000 |
| Row/column relation presence | 15/15 = 1.0000 |
| Cells with inferred header path | 0.5830 |
| Caption relation | N/A: source adapter does not provide canonical caption edges |
| Footnote relation | N/A: source adapter does not provide canonical footnote edges |
| BBox/geometry | N/A: TAT-QA source has no cell geometry |
| External canonical cell accuracy | N/A: no independent canonical cell annotation |

This proves preservation of the source array and identity relations, not that a general PDF parser can reconstruct arbitrary merged cells, footnotes, or geometry. On the HSBC corpus, the existing parser still produces page text only; `verified_structured_table_ir = N/A`, so E0 structured-table routes are recorded as unavailable rather than silently redirected to Parsed Page Text.

## 3. HSBC failure-routing experiment

The frozen `HSBCVisualStress-v1` was used unchanged: 60 cases, ten categories, six cases per category. Visual candidates are the same real rendered page images used by B3. CLIP is the existing `openai-clip-RN50` CPU adapter; no model replacement or benchmark tuning was performed.

### 3.1 Retrieval and route results

| Policy | R@1 | R@5 | R@10 | R@50 | Critical coverage | Eligible rate | Visual invocation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Always Text | 0.0000 | 0.0000 | 0.0000 | 0.1167 | 0.0000 | 0.0000 | 0.0000 |
| Coverage → Vision | 0.0167 | 0.0500 | 0.1000 | 0.5833 | 0.1000 | 0.1000 | 1.0000 |
| Always Vision | 0.0167 | 0.0500 | 0.1000 | 0.5833 | 0.1000 | 0.1000 | 1.0000 |
| E0 Oracle Failure Router | 0.0167 | 0.0167 | 0.0500 | 0.3000 | 0.0500 | 0.0500 | 0.5000 |
| E1 Predicted Failure Router | 0.0167 | 0.0333 | 0.0833 | 0.3833 | 0.0833 | 0.0833 | 0.5000 |

E0 invokes structured retrieval for 24/60 table cases, adjacent-page retrieval for 6/60 page-fragmentation cases, and visual retrieval for 30/60 chart/layout cases. Because HSBC has no verified Table IR, the 24 structured invocations have no structured candidates. E1 invokes text retry for 24/60, adjacent-page retrieval for 6/60, and visual retrieval for 30/60. E1 route accuracy against the gold failure category is 0.5000; this is a diagnostic baseline, not a trained classifier.

### 3.2 Recovery and regression

Recovery is reported at the actual evaluation cutoffs, not one ambiguous cutoff:

| Policy | Recovery@1 | Recovery@5 | Recovery@10 | Recovery@50 | Regression@50 | Net@50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Coverage → Vision | 1 | 3 | 6 | 31 | 3 | +28 |
| Always Vision | 1 | 3 | 6 | 31 | 3 | +28 |
| E0 Oracle Failure Router | 1 | 1 | 3 | 14 | 3 | +11 |
| E1 Predicted Failure Router | 1 | 2 | 5 | 18 | 2 | +16 |

The E1 critical-requirement recovery rate is 0.0833, regression rate at the evaluated critical gate is 0.0000, and net recovery is +5 cases under the runner's `@10` critical-coverage comparison. Page recovery and critical evidence qualification remain separate metrics.

## 4. Per-failure-type result

All categories contain six real HSBC page cases. The following is page Recall@10; `Text` is the Always Text policy, `Vision` is Always Vision, and `E1` is the predicted route.

| Failure type | Text | Vision | E0 | E1 |
| --- | ---: | ---: | ---: | ---: |
| CAPTION_MISMATCH | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| CHART_LEGEND | 0.0000 | 0.1667 | 0.1667 | 0.1667 |
| CHART_VALUE | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| FOOTNOTE_LOSS | 0.0000 | 0.1667 | 0.0000 | 0.0000 |
| MULTI_COLUMN_READING_ORDER | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| MULTI_LEVEL_HEADER | 0.0000 | 0.3333 | 0.0000 | 0.3333 |
| TABLE_COLUMN_MIXING | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| TABLE_ROW_MIXING | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| UNIT_HEADER_LOSS | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| VISUAL_ONLY_INFORMATION | 0.0000 | 0.3333 | 0.3333 | 0.3333 |

The current E1 heuristic recognizes explicit chart/figure cues but misses table/layout categories when the wording is generic. That is consistent with the purpose of B4: it localizes the need for a better failure signal, rather than claiming that the first router is solved.

## 5. Representative bad cases

The complete rows, rankings, and provenance are in the formal run traces. Representative cases include:

- `hsbc-v-0013`, `MULTI_LEVEL_HEADER`, gold `hsbc-fy2025-annual-report:p14`: E1 chose visual retrieval; E0 correctly identifies that the available remedy should be structured retrieval. This is a direct example of missing Table IR causing route substitution.
- `hsbc-v-0033`, `CHART_VALUE`, gold `hsbc-fy2025-annual-report:p33`: both E0 and E1 choose visual retrieval and recover the gold page at the tested recovery cutoff. This is the cleanest observed vision-requiring category in this workload.
- `hsbc-v-0049`, `MULTI_COLUMN_READING_ORDER`, gold `hsbc-fy2025-annual-report:p35`: E0 chooses visual retrieval, while E1 falls back to text retry. The case remains a predicted-router miss.
- `hsbc-v-0001`, `TABLE_ROW_MIXING`, gold `hsbc-fy2025-annual-report:p2`: E0 chooses structured retrieval, but structured Table IR is unavailable on HSBC. The system therefore exposes a missing capability instead of treating page text as a table solution.
- At `@50`, the multimodal path introduces regressions on `hsbc-v-0004` (TABLE_ROW_MIXING, gold p5), `hsbc-v-0041` (CHART_LEGEND, gold p41), and `hsbc-v-0045` (CAPTION_MISMATCH, gold p45). At `@10`, the formal E1 critical comparison records zero regression.

## 6. Latency and cost proxy

Measured on CPU with the existing CLIP RN50 adapter. Offline visual indexing is reported separately from query latency.

| Component | P50 ms | P95 ms |
| --- | ---: | ---: |
| Text retrieval | 191.40 | 253.82 |
| Structured-table retrieval | N/A | No HSBC Table IR |
| Adjacent-page retrieval | 179.90 | 211.08 |
| Visual retrieval | 94.24 | 271.79 |
| Routing | 0.0008 | 0.0011 |
| Evidence qualification | 5.53 | 9.70 |
| End-to-end | 516.79 | 977.33 |

Offline visual indexing took 6,959.86 ms for 78 candidate pages in the formal second run. Visual invocation was 100% for coverage→vision/always-vision, 50% for E0 and E1. No monetary cost estimate is claimed because this is local CPU inference and no token billing exists.

## 7. FinRAGBench-V public-corpus investigation

The public dataset remains frozen at `zhaosuifeng/FinRAGBench-V`, revision `d0d65255c94e687caa81ac9da7758ed25ff046a5`, with the existing 100-query slice and qrels unchanged. The new non-destructive inspection queried the official Hugging Face tree for `corpus/en` and saved `data/finragbench_v_source/corpus_layout_investigation.json`.

Observed facts:

- the 100-query qrels contain 607 rows and 504 unique English corpus IDs;
- the pinned `corpus/en` tree exposes `part_0000` through `part_0013`, 13 shards of exactly 5 GiB and one shard of 2,825,689,504 bytes;
- a range probe returned HTTP 206 and gzip magic bytes, confirming shard-level compressed transport;
- no individually addressable page-image paths are exposed in that tree, so selecting 100 pages still requires access to their containing compressed shard(s);
- no shard was downloaded, no slice was changed, and no public score was fabricated.

Therefore FinRAGBench-V public page-image evaluation remains `N/A` and is still a B3 external blocker, not a B4 result.

## 8. Reproducibility

Formal runs:

- `artifacts/b4_runs/20260914T003834/`
- `artifacts/b4_runs/20260914T003956/`

Both use commit `8bee650`, the same config, frozen HSBC evidence/render manifests, CPU OpenAI CLIP RN50, and 60 stress cases. `metrics.json` and `failure_cases.jsonl` are semantically identical across the pair. The per-query trace differs only in measured timing fields; therefore exact byte identity is not claimed for timing-bearing traces. Both runs report the same Table IR metrics, route metrics, rankings, and failure rows.

Verification performed after implementation:

```text
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m compileall -q src tests scripts
openspec validate b4-structure-preserving-evidence-ir-failure-aware-escalation --type change --strict --no-interactive
git diff --check
```

## 9. Supported and rejected claims

Supported:

- A source-array Table IR can preserve cell identity and row/column relationships on the available TAT-QA source tables.
- HSBC's current page-text parser does not provide verified Table IR; this is a measurable blocker for table-specific recovery.
- In this stress workload, explicit chart/visual categories are the clearest cases where visual retrieval adds recovery, while table/layout categories require structure or better failure signals.
- Failure-aware routing can reduce visual invocation from 100% to 50% in this workload, but the current E1 router has only 0.5000 route accuracy and the result is not a cost-saving production claim.

Rejected:

- Vision is not shown to be generally superior to text.
- E0 is not a deployable router; it uses gold failure categories and is evaluation-only.
- E1 is not a learned failure classifier.
- TAT-QA source-array round-trip does not prove arbitrary PDF table reconstruction, merged-cell semantics, footnotes, or geometry.
- FinRAGBench-V public evaluation is not complete.

## 10. B4 decision and hypothesis

**B4 = COMPLETE for the scoped experimental phase.** The phase delivered the structure-preserving IR contract, oracle and predicted failure-routing paths, qualification-aware recovery metrics, provenance-bearing artifacts, public-corpus investigation, tests, and two fixed-code runs.

The central hypothesis **survives in qualified form**: a critical evidence miss should be diagnosed before escalating to vision, because table failures need a real Table IR and visual failures are a narrower subset. The stronger hypothesis that a lightweight query heuristic already routes these failures reliably does **not** survive: E1 route accuracy is 0.5000, and HSBC structured retrieval remains unavailable. B3 stays `PARTIAL`; B4 does not authorize production hardening. The next justified work is improving verified document structure and failure signals, not adding a larger model or UI.
