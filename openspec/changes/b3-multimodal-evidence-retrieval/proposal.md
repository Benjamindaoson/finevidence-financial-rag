# B3 — Multimodal Evidence Retrieval & Visual Grounding

## Problem

Text extraction can lose table geometry, chart values, captions, and reading order even when parsing completes successfully. P0-H established that evidence relevance is not enough; B3 tests whether page images recover those failures while preserving evidence qualification and avoiding an unconditional visual-inference cost.

## Scope

Implement deterministic PDF page rendering, image-backed Evidence IR, a real image encoder baseline, text/structured/visual retrieval baselines, normalized fusion, conditional routing, citation evaluation, structure-fidelity checks, and cost/latency instrumentation. The real HSBC FY2025 corpus is the primary executable stress set. FinRAGBench-V metadata is fixed as a public source slice; its multi-gigabyte PDF archive is not silently represented as downloaded local data when unavailable.

## Non-goals

No GraphRAG, agents, ACL, serving stack, full visual generation, or production deployment is introduced by this change.

## Acceptance

- Page rendering is byte-stable and records source/render provenance.
- Visual retrieval consumes page image bytes through a real image encoder, or is explicitly N/A with a technical blocker.
- T0/T1/V0/M0/M1 are evaluated on a real page-image corpus.
- Visual recovery, critical recovery, regression, citation, structure fidelity, and latency are emitted as reproducible artifacts.
- Two formal runs use immutable manifests and a single code commit.
