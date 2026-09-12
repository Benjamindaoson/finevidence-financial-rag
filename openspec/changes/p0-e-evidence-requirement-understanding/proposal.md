# P0-E Evidence Requirement Understanding

## Why

P0-D showed that gold-fact targeted retrieval can recover most complete evidence, while the deterministic question decomposer has Required Fact Recall `0.0017`. The next bottleneck is therefore understanding the evidence required by a question, not adding another retrieval component.

## What changes

- Add a structured fact-slot contract for `fact_type`, `entity`, `metric`, `period`, `segment`, `basis`, `role`, and `critical`.
- Compare D0 heuristic, D1 LLM-direct (explicitly `N/A` without an authorized provider), D2 schema-constrained, and D3 evidence-aware decomposition.
- Add fact detection precision/recall, critical-fact recall, slot accuracy, evidence completion, FAER, and Oracle Gap reporting.
- Keep public, controlled, and HSBC results in separate artifacts.
- Add an HSBC official-source manifest/fetch contract without redistributing HSBC documents.

## Out of scope

- No Agent loop, GraphRAG, ACL, FastAPI, Kubernetes, or full FinRAGBench-V corpus.
- No claim of generation, visual retrieval, citation bbox, or LLM quality without an actual configured experiment.
