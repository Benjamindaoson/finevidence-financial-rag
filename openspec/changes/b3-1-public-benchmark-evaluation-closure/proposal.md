# B3.1 — Public Benchmark & Evaluation Closure

## Why

B3 has a real image encoder and an executable HSBC stress track, but its public FinRAGBench-V page-image slice is still unavailable and its first runner mixed stress and routing workloads. B3.1 closes only those evaluation gaps without changing the B3 retrieval design.

## Scope

- Pin the existing 100-query FinRAGBench-V slice to a dataset revision and use the official Hugging Face cache/Xet downloader for its single PDF archive.
- Rename the non-structured T1 adapter to `T1 Parsed Page Text` and report verified structured Table IR as N/A.
- Make recovery metrics explicit at @1, @5, and @10.
- Add a balanced, real-page `HSBCMultimodalRouting-v1` evaluation track.
- Instrument query components and offline indexing separately, then run reproducibility checks.

## Non-goals

No new visual model, VLM serving stack, verified table parser, production hardening, or full FinRAGBench-V corpus download is part of this change.
