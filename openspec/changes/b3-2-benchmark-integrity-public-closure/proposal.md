# B3.2 — Benchmark Integrity & Public Closure

## Why

B3.1 established executable visual retrieval results on a project-created HSBC stress set, but the stress construction may itself bias the comparison and the public FinRAGBench-V page-image slice remains unclosed. This change audits those claims without changing the frozen B3.1 datasets or models.

## Scope

- Freeze a performance-blind, corpus-derived HSBC natural multimodal control set.
- Attribute a fixed sample of HSBCVisualStress-v1 failures using source and ranking evidence.
- Attempt the pinned FinRAGBench-V archive through an alternate resumable transport and preserve blocker evidence if it remains unavailable.
- Report stress, natural-control, and public results separately.

## Non-goals

No model replacement, benchmark retuning, production serving, structured-table implementation, UI, GraphRAG, or agent framework is part of B3.2.

## Status

The public closure may remain blocked by transport. A blocked public archive is reported as such; it is never represented as a completed evaluation.
