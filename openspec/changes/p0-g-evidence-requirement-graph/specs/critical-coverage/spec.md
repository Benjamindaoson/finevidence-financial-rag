# Critical coverage

## ADDED Requirements

### Requirement: Gate on critical requirements
Answer eligibility MUST require every critical requirement to be independently satisfied; supporting or optional omissions may produce a partial result.

#### Scenario: Critical denominator missing
- **WHEN** numerator evidence is present but the critical denominator is missing
- **THEN** `answer_eligible` is false and `CRITICAL_REQUIREMENT_MISSING` is emitted

### Requirement: Report critical metrics
The evaluator MUST report Critical Coverage Rate, Critical Missing Rate, and Critical Fact Recall separately from raw self-coverage.

#### Scenario: Supporting context missing
- **WHEN** all critical requirements are independently satisfied but a supporting context requirement is absent
- **THEN** answer eligibility remains true and the partial context omission is visible in the trace
