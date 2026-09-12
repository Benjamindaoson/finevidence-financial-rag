## 1. Public source manifest and raw-data audit

- [x] Add TAT-QA and FinQA source audit with repository commit, file hash, size, counts, and readiness status.
- [x] Verify both public source repositories and record exact raw dev hashes.

## 2. Public record adapter and RealFinance-v1 slice

- [x] Add TAT-QA table-text projection preserving table and related paragraph evidence.
- [x] Add FinQA projection preserving `gold_inds`, `program`, `exe_ans`, and source IDs.
- [x] Build and verify a fixed 50 TAT-QA + 50 FinQA slice with a derived manifest.

## 3. Required fact and facet evaluation

- [x] Add deterministic required-fact decomposer and omitted-fact precision/recall metrics.
- [x] Add separate predicted-facet ranking condition and canonical-label `N/A` behavior.

## 4. P0-D runner and gates

- [x] Add runner for public-slice ranking, gold/predicted fact coverage, traces, and failure cases.
- [x] Add HSBC readiness gate with `LOCAL_PROVENANCE_SOURCE_MISSING` when no licensed local corpus is available.
- [x] Avoid full FinRAGBench-V download and keep controlled fixture results separate.

## 5. Verification and report

- [x] Run focused RED/GREEN tests and full regression.
- [x] Run the same configuration twice and compare metrics/manifests.
- [x] Validate OpenSpec, CodeGraph, diff, working tree, and write the external-validity report.
