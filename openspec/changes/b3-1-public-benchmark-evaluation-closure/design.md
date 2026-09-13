# Design

The existing B3 runner remains the execution entry point. It uses the frozen HSBCVisualStress-v1 cases and, when present, an additional routing dataset. Ranking metrics for the original stress set remain isolated from the routing workload.

## Contracts

- `FinRAGBench-V-Slice-v1` records the source commit, source-file hashes, archive hash/status, and never silently claims page-image evaluation when the archive is unavailable.
- T1 is a parsed page-text adapter only. No cell identity, row/column relation, header relation, unit edge, or table geometry is claimed.
- Recovery is reported at K in `{1,5,10}`. The denominator is the number of text failures at the same K; regression is also measured at the same K.
- Routing gold labels are evaluation-only. `route_query` receives the question, parser confidence, and qualified initial coverage, never the gold modality.
- Latency has separate P50/P95 samples for text retrieval, parsed-page retrieval, visual query encoding/retrieval, fusion, routing, evidence qualification, and end-to-end query time. Fit/indexing time is reported separately.

## Public data

The downloader uses `huggingface_hub.hf_hub_download` with `hf_xet`, a pinned commit revision, a project-local cache, and non-overwriting local artifacts. A failure writes `data/finragbench_v_source/download_blocker.json` with the exception and traceback.

## Acceptance

- A successful public run has page-image rankings for T0/T1/V0/M0/M1 on the frozen 100-query slice; otherwise the blocker remains explicit.
- The HSBC stress set remains 60 cases and the routing set is separate and balanced when its real-page mining succeeds.
- Run artifacts include manifests, rankings, traces, recovery@K, routing, citation, and latency evidence.
