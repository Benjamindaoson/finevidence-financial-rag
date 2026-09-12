## ADDED Requirements

### Requirement: Required facts accept alternative evidence
The system SHALL represent each required fact with `fact_id`, `description`, and one or more `acceptable_evidence_ids`; a fact SHALL be covered when any acceptable evidence ID is selected.

#### Scenario: Alternative evidence covers one fact
- **WHEN** a selected evidence ID appears in a fact's acceptable evidence list
- **THEN** the fact is marked covered even if other acceptable IDs were not selected

#### Scenario: No acceptable evidence is selected
- **WHEN** none of a fact's acceptable evidence IDs is selected
- **THEN** the fact is marked missing and the case is incomplete

### Requirement: Coverage metrics use answerable cases only
The system SHALL calculate FactCoverage, InitialCompleteEvidenceRate, FinalCompleteEvidenceRate, PartialToCompleteRecoveryRate, and FalseAnswerEligibilityRate using explicit answerable-case denominators.

#### Scenario: Partial case is recovered
- **WHEN** an answerable case has 2 of 3 facts initially and all 3 after targeted retrieval
- **THEN** initial coverage is 2/3, final coverage is 1.0, and the case counts as a partial-to-complete recovery

#### Scenario: Incomplete case is blocked
- **WHEN** an answerable case is missing at least one fact and the coverage gate evaluates eligibility
- **THEN** eligibility is false and the case contributes zero to false-answer eligibility

### Requirement: False Answer Eligibility is visible
The system SHALL report the rate of answerable cases that are incomplete but marked eligible by each policy, including the denominator and ineligible case IDs.

#### Scenario: Top-K policy exposes unsafe eligibility
- **WHEN** an any-fact policy marks a partial case eligible
- **THEN** that case is counted in FalseAnswerEligibilityRate

#### Scenario: Coverage policy blocks unsafe eligibility
- **WHEN** an all-facts policy evaluates the same partial case
- **THEN** the case is ineligible and FalseAnswerEligibilityRate is zero for that case
