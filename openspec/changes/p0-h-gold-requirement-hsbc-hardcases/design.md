# Design

## Requirement adjudication

Select a real, existing subset from `RealFinance-v1`, preserving source case IDs and dataset hashes. Generate Pass A and Pass B from the question, gold answer/program and supporting evidence only; neither pass reads the other. Adjudication resolves disagreements deterministically from source evidence and records the disagreement rather than hiding it. The result uses `RequirementAdjudicated-v1`, with `human_verified=false`.

## Matching and evaluation

Match predicted and adjudicated requirements with a one-to-one bipartite assignment. A match requires compatible fact type/role and compatible populated slots, with description similarity as a supporting signal. Reuse of one predicted or gold requirement is forbidden. Requirement metrics and Independent/Critical Coverage metrics are reported separately; missing canonical slots remain `N/A`.

## D1

The runner accepts a local Transformers model path and uses `temperature`-free greedy generation with a versioned prompt and JSON schema. A bounded malformed-JSON repair path may retry once with the same model and a stricter JSON instruction. If the existing small local cache cannot run after minimal dependency installation, D1 remains `N/A` with the exact blocker.

## HSBC corpus and hard cases

Download only URLs in `data/hsbc_public_sources.json` to ignored `artifacts/hsbc_local_sources/`. Hash each file, record page count, and parse pages into evidence blocks that retain document/page/source hash. A hard case must have one real positive and at least one real high-similarity negative with an evidence-backed facet conflict; all candidate text must originate from parsed blocks. Verification passes are model-assisted and non-human.

## B3 gate

Set B3 `READY` only when RequirementAdjudicated-v1 exists, independent coverage is validated, HSBC provenance is fixed, and HSBCNaturalHard-v1 has at least 50 valid cases. This change does not start B3 implementation.
