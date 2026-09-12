# P0-G Evidence Requirement Graph & Fact-Evidence Alignment

## Why

P0-E exposed a false-completeness failure: D3 can let one candidate evidence item cover several semantically different predicted facts. A flat acceptable-evidence list cannot distinguish direct support, derivation inputs, explanatory support, or invalid reuse.

## What changes

- Add a backward-compatible structured requirement schema with fact type, role, financial slots, operation, criticality, dependencies, and acceptable evidence IDs.
- Add a Python/Pydantic DAG for requirement dependencies and derived facts.
- Add explicit fact-evidence alignments, support types, slot matches, and bounded evidence reuse policy.
- Add raw self-coverage, independent coverage, critical coverage, reuse metrics, FAER, warnings, and compatible Oracle Gap fields.
- Add D4 Requirement-Graph-Constrained decomposition and a bounded deterministic targeted retrieval loop.
- Add a 20-case manually annotated `RequirementGold-v1` subset only if labels can be provenance-linked; otherwise keep structured gold metrics `N/A`.
- Keep HSBC as a URL-only/local provenance track; do not commit PDFs.

## Out of scope

- No Neo4j, GraphRAG, Agent framework, VLM, visual embedding, ACL, FastAPI, Kubernetes, new RAG framework, or full FinRAGBench-V corpus.
