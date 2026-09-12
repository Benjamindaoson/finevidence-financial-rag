# P0-G Evidence Requirement Graph & Fact–Evidence Alignment

## Goal

Make answer eligibility depend on role-correct, independently justified evidence or legal derivation, and measure the gap between raw self-coverage and valid critical coverage on the frozen RealFinance-v1 slice.

## Frozen boundaries

- Do not change TAT-QA, FinQA, or RealFinance-v1 source data.
- Keep D1 `N/A` unless a suitable local LLM is already available.
- Keep targeted retrieval deterministic and bounded to two rounds.
- Do not enter B3 visual retrieval or add an agent/framework/database layer.
- Keep RequirementGold-v1 `N/A` until manual annotation provenance exists.

## Execution tasks

1. Add Pydantic requirement, edge, graph, alignment, reuse-event, and coverage contracts.
2. Add DAG validation, deterministic alignment, reuse policy, derived-fact propagation, and critical gate.
3. Add D4 question-type templates and P0-G artifact writer.
4. Add focused tests before implementation and rerun them after implementation.
5. Run the frozen public benchmark slice; retain initial/final evidence and per-query trace.
6. Run the same configuration twice and compare metrics, manifest, and trace counts.
7. Update the P0-G report, README, strategy, benchmark plan, and chat knowledge base.
8. Validate tests, compilation, OpenSpec, CodeGraph, diff, and repository status; commit the result.

## Acceptance evidence

- A fixture proves raw self-coverage can exceed independent coverage due to invalid reuse.
- A derived requirement is satisfied through independent inputs without direct evidence.
- Missing critical evidence blocks `answer_eligible`; missing supporting evidence does not.
- Metrics distinguish Gold Independent CER, Predicted Independent CER, critical coverage, reuse, and gaps.
- Two reproducibility runs are recorded with exact paths and the implementation commit.
