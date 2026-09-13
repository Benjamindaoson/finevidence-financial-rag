# B4.1 — Real Financial Table Recovery & Executable Structured Retrieval

## Why

B4 proved that routing and visual retrieval are not substitutes for a structure-preserving executor. Its HSBC table-failure track still reported `structured_table_ir = N/A` because the available evidence was page text only.

## Scope

Build a bounded, deterministic PDF-to-TableIR path over the existing public HSBC Annual Report artifact, compare it with the frozen text and visual baselines, and send structured candidates through the existing Evidence Qualification contract.

This change does not reopen B3, alter frozen B4 data, introduce a production serving layer, or claim verified semantic table accuracy without human gold.

## Success criteria

- Real PDF words and geometry produce auditable TableIR cells with stable provenance.
- T2 is a real TableIR executor, not a renamed page-text retriever.
- T2, text, visual, and T2+text page retrieval and qualification results are reproducible.
- Structure fields without verified annotation are reported as `N/A`.
- FinRAGBench-V remains an external blocked track and is not silently substituted.
