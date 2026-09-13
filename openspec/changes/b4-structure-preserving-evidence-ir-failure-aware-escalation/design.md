# Design

## Frozen inputs

P0-H, B3.1, B3.2, `HSBCVisualStress-v1`, `HSBCNaturalMultimodal-v1`, HSBC PDF/render manifests, and CLIP RN50 are unchanged. FinRAGBench-V remains a separate external-blocker track at its frozen revision.

## Table IR

`TableIR` preserves a real source table as a grid of `TableCell` records with stable cell IDs, row/column identity, header hierarchy, raw values, detectable period/unit annotations, and source provenance. Caption, footnote relation, and bbox are nullable and remain N/A when the source does not supply them. A round-trip invariant checks that no source cell is silently dropped or reordered.

The TAT-QA source table arrays are used for this structural integrity experiment; the HSBC page parser currently has no verified table cells and is not promoted to Table IR.

## Failure routing

The oracle router receives only the evaluation category to estimate upper-bound routing value. The predicted router receives question text, initial retrieval observations, and parser availability; it never receives the gold category. Actions are `TEXT_RETRY`, `STRUCTURED_TABLE_RETRIEVAL`, `ADJACENT_PAGE_RETRIEVAL`, `VISUAL_RETRIEVAL`, and `ABSTAIN_ESCALATE`.

Every action re-enters the existing page/evidence qualification contract. A structured action against a corpus with no verified Table IR records an unavailable action rather than silently falling back under a structured name.

## Acceptance

- E0 and E1 report recovery, independent critical coverage, net recovery, wrong escalation, invocation, regression, and latency.
- Table IR reports exactly which relations are preserved and which remain N/A.
- Oracle results are separated from predicted-router results.
- A negative or non-improving oracle result is retained as a valid stop/go result.
