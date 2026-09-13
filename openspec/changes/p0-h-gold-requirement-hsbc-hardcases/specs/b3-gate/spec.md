# B3 gate

## ADDED Requirements

### Requirement: B3 MUST remain blocked without evidence foundations
B3 MUST be `READY` only when RequirementAdjudicated-v1 exists, Independent Coverage has been validated, HSBC provenance is fixed, and HSBCNaturalHard-v1 has at least 50 valid cases.

#### Scenario: any required foundation is absent
- **WHEN** one of the required foundations is missing
- **THEN** `b3_gate.json` MUST report `BLOCKED` and name the missing gate
