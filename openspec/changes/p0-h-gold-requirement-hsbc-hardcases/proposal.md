# P0-H Gold Requirement Validation & HSBC Natural Hard Cases

## Why

P0-G demonstrated that raw self-coverage can be inflated by invalid evidence reuse, but RealFinance-v1 has no canonical requirement labels and D1 has never run a real local language model. HSBC provenance is also URL-only, so the financial facet/ranking result has not yet been tested on naturally occurring public disclosure hard negatives.

## What changes

- Create `RequirementAdjudicated-v1` from a bounded, balanced RealFinance-v1 subset using two independent model-assisted passes and a separate adjudication pass.
- Add one-to-one requirement matching and requirement understanding metrics for D0–D4.
- Add a real local D1 direct decomposition baseline when an already available small model can run; otherwise record a technical N/A with attempted runtimes and models.
- Download only the verified HSBC FY2025 Annual Report and Pillar 3 disclosures, record file/page/hash provenance, and parse a minimal page/block evidence pool.
- Mine and adjudicate `HSBCNaturalHard-v1` from real HSBC blocks; evaluate dense, hybrid, predicted-facet, and adjudicated-facet ranking with per-category hard-negative metrics.
- Produce explicit reproducibility artifacts and a B3 gate decision without implementing visual retrieval.

## Out of scope

- No GraphRAG, Neo4j, multi-agent framework, ACL/ABAC, FastAPI, Kubernetes, full serving stack, full FinRAGBench-V download, or visual retrieval implementation.
- `RequirementAdjudicated-v1` is not human gold: `human_verified=false` and `annotation_method=dual_pass_model_assisted_adjudication`.
- `HSBCNaturalHard-v1` is a project-created stress benchmark from public HSBC disclosures, not an HSBC-official benchmark.
