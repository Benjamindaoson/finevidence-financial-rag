## 1. Fact coverage contract

- [x] 1.1 Add `FactRequirement` and backward-compatible `MiniCase.required_facts` validation.
- [x] 1.2 Add fact coverage matrix with alternative evidence IDs and missing-fact descriptions.
- [x] 1.3 Add Initial CER, Final CER, Partial-to-Complete Recovery, and FAER metrics with explicit answerable denominators.
- [x] 1.4 Confirm MiniBench-v1 files and manifest remain byte-for-byte unchanged.

## 2. Targeted evidence recovery

- [x] 2.1 Add 30–50 fixed EvidenceCompleteness-v1 multi-fact cases and a verified manifest.
- [x] 2.2 Implement missing-fact query construction and bounded two-round targeted retrieval.
- [x] 2.3 Persist initial, per-round, and final coverage/evidence traces.
- [x] 2.4 Test one-round recovery, incomplete two-round stop, and duplicate evidence merge.

## 3. Financial hard-negative ranking

- [x] 3.1 Add explicit FinancialFacets and deterministic query/candidate facet extraction.
- [x] 3.2 Add exactly 100 FinanceHardSet-v1 cases across the frozen confusion categories.
- [x] 3.3 Implement facet-aware reranking and pairwise hard-negative-aware reranking.
- [x] 3.4 Test reproducibility, positive/negative ordering, and per-category HN Error.

## 4. Experiment tables and verification

- [x] 4.1 Implement one P0-B/P0-C runner that does not invoke B3 or visual retrieval.
- [x] 4.2 Emit ranking and sufficiency tables plus per-query/per-round traces and standard run artifacts.
- [x] 4.3 Run each experiment twice with the same config and verify stable metrics and distinct run directories.
- [x] 4.4 Run full tests, OpenSpec strict validation, CodeGraph status, and Git status; record blockers and observed results only.
