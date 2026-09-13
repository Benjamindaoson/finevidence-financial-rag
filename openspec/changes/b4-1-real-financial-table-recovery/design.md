# Design

## Table recovery

`pdfplumber` supplies positioned words and candidate table regions from the frozen HSBC Annual Report PDF. Numeric column anchors are inferred from x coordinates and row groups from y coordinates. The result is converted to the existing `TableIR` contract and each cell retains `table_id`, `row_id`, `column_id`, `bbox`, page, and source PDF identity.

This is geometry-assisted recovery, not a verified semantic table parser. Merged-cell semantics, footnote links, and semantic cell correctness remain explicitly unverified.

## Structured executor

`StructuredTableRetriever` indexes TableIR cell evidence whose text includes row label, header path, value, unit, period, and cell identity. Its deterministic lexical score is intentionally named as such. It ranks cells, not flattened page text, and emits Evidence objects that pass the existing alignment and independent-coverage gate.

## Evaluation

T0 and T1 reuse the existing HSBC page-text evidence with their frozen retriever settings. V0 reuses the real CLIP page-image retriever. T2+Text uses RRF after rank-based fusion; raw scores are never added. T2 table candidates are accepted by page-level gold only when they are on the gold page and also pass the existing lexical alignment check. The evaluator reports page recall, MRR, nDCG, critical coverage, recovery at 1/5/10, regression, and component latency.

The Oracle Table Executor is a diagnostic route selected by the frozen category labels; it is not a deployable router. Predicted routing is measured only as an observation because this workload does not justify promoting the heuristic.

## Reproducibility boundary

PDF SHA256, page scope, rendering/evidence manifest hashes, code commit, model manifest, TableIR JSONL, rankings, traces, and latency outputs are written under an ignored run directory. No PDF is committed.
