# Design

## Requirement schema

`Requirement` is separate from the legacy `FactRequirement` so MiniBench, controlled fixtures, and RealFinance-v1 remain loadable byte-for-byte. It contains `requirement_id`, description, `RETRIEVED_FACT`/`DERIVED_FACT`/`EXPLANATORY_FACT`/`CONTEXT_FACT`, role, financial slots, operation, criticality, `depends_on`, and acceptable evidence IDs.

## Requirement graph

`RequirementGraph` stores requirements and typed edges (`DEPENDS_ON`, `DERIVED_FROM`, `EXPLAINS`, `COMPARED_WITH`). Pydantic validation rejects duplicate IDs, unknown endpoints, self-edges, and cycles. Derived requirements are complete only when all dependencies are independently complete; they do not require a direct document chunk.

## Alignment and reuse

`FactEvidenceAlignment` records support type, score, matched/mismatched slots, reuse eligibility, and reason. The reuse policy allows reuse only when the evidence explicitly supports compatible role/period/metric/entity slots; a lexical overlap alone never permits reuse. Invalid reuse events are excluded from independent coverage and emitted in the trace.

## Coverage

The runner reports raw self-coverage, gold evidence coverage, independent complete evidence rate, critical coverage, evidence reuse rate, invalid reuse rate, FAER, and both old and calibrated Oracle Gap fields. Missing critical requirements force `answer_eligible=false`; missing supporting requirements can leave a partial result.

## D4 and annotation boundary

D4 uses fixed question-type templates and a requirement graph. Its deterministic targeted retrieval adds at most two rounds and re-aligns evidence after each round. There is no agent loop. TAT-QA/FinQA structured slot gold is absent; slot and criticality metrics remain `N/A` until the optional 20-case `RequirementGold-v1` annotation subset exists with source IDs, method, timestamp, and hash.
