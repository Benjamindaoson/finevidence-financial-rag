# FinEvidence Human-Verified Final Results

Status: **NOT STARTED — HUMAN REVIEW REQUIRED**

This document is the destination for the final three trust-boundary results.
It is deliberately not a results claim: no human annotation row currently
exists in the repository with `human_verified=true`.

## Review package

Start the local workbench from the repository root:

```powershell
& .venv\Scripts\python.exe -m uvicorn finevidence.api.app:app --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/review` and choose one track at a time. The package
contains:

- 50 claim citation candidates from frozen RealFinance-v1;
- 24 real HSBC B4.1 TableIR regions with page-image links;
- 60 balanced answerability candidates from real questions under explicit
  scoped evidence-availability conditions: 20 answerable, 20 partial and 20
  proposed unanswerable.

The last two classes are candidate labels, not facts. The reviewer must decide
whether the available evidence makes the question partial or unanswerable.

## Promotion rules

Use `Save` for an unfinished row, `Needs Review` for uncertainty and `Skip`
only when the row cannot be assessed. Use `Confirm & Save` only after checking
the original evidence. The server, rather than the browser payload, derives
`human_verified` from the final status.

## Final tables

Until the review files are populated, all values below remain `N/A`.

| Track | Metrics | Current status |
|---|---|---|
| Claim citation | Citation P/R/F1, Claim Support Rate, Unsupported Citation Rate, Page/Block/Cell Accuracy | N/A; no verified gold |
| Table semantics | Cell, row, column, header, unit, period, entity, merged-cell, footnote accuracy | N/A; no verified gold |
| Answerability | Action Accuracy, Abstention P/R/F1, False Answer, False Abstention, Partial Detection | N/A; no verified gold |

Run the existing final evaluator after review records are complete. It will
automatically consume the latest `human_verified=true` rows, pair citation
gold with the preserved historical Top-K prediction IDs, and keep fields
without applicable gold as `N/A`.
The previous P0/B3/B4/P0-J candidate metrics are preserved in
`docs/FIN_EVIDENCE_FINAL_RAG_EVALUATION.md` and are not overwritten here.
