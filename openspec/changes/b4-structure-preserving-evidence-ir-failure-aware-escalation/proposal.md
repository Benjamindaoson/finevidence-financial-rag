# B4 — Structure-Preserving Evidence IR & Failure-Aware Escalation

## Why

B3.2 showed that an evidence miss is not equivalent to a need for vision. Natural HSBC pages favored parsed text, while the stress workload mixed table structure, page fragmentation, layout, and chart failures. B4 tests whether the system can preserve available table relations and choose a recovery action that matches the diagnosed failure.

## Scope

- Implement a minimal structure-preserving financial Table IR over real TAT-QA source tables.
- Run an oracle failure router over the frozen HSBCVisualStress-v1 categories.
- Run a performance-blind predicted failure router using only query and observed retrieval signals.
- Compare text retry, structured-table, adjacent-page, visual, and abstain/escalate paths with evidence qualification.

## Non-goals

No GraphRAG, agent framework, production serving, ACL, UI, model replacement, or FinRAGBench-V slice modification.

## Status

B4 is an experimental phase. It does not imply production readiness.
