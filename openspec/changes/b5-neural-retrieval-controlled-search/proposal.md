# B5 — Neural Retrieval & Controlled Agentic Search

## Why

FinEvidence already provides evidence qualification, independent coverage,
failure attribution, provenance, and frozen financial evaluation suites. Its
retrieval backends are intentionally conservative CPU baselines. B5 tests
whether modern neural retrieval and bounded search control add measurable
value without weakening the evidence contract.

## Scope

- real model adapters for neural dense retrieval, optional reranking, and
  optional late interaction;
- conditional visual retrieval only when an image-consuming checkpoint is
  runnable and its value is measured;
- a deterministic-control-first typed search controller;
- an optional lightweight in-memory evidence graph for measured
  cross-document gaps;
- stage-specific frozen experiments, failure attribution, and cost/latency.

## Out of scope

Graph databases, multi-agent frameworks, unrestricted LLM tool loops, new
frontends, ACL/ABAC, production serving infrastructure, and changing any
historical benchmark or result.

## Success criteria

Every promoted intervention must show a reproducible quality or failure
recovery benefit on a frozen benchmark, preserve Evidence Qualification and
provenance, and report its latency/cost tradeoff. Unavailable models or
unverifiable gains remain `N/A`, `REJECT`, or `INCONCLUSIVE`.
