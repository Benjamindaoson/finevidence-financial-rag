# Evaluation Contracts

## ADDED Requirements

### Requirement: Citation metrics require explicit gold status

The evaluator MUST refuse to label candidate-only citation annotations as human-verified gold metrics.

#### Scenario: Candidate citation annotations

- **WHEN** citation records have human_verified=false
- **THEN** final citation precision, recall, F1, and claim support metrics are N/A
- **AND** the run records the human verification blocker

### Requirement: Table semantic fields preserve N/A

The evaluator MUST compute field accuracy only from non-null verified labels and MUST keep structural invariants separate.

#### Scenario: No verified cell labels

- **WHEN** all semantic field labels are null or human_verified=false
- **THEN** semantic accuracy is N/A
- **AND** structure recoverable rate is reported independently

### Requirement: Answerability metrics use action labels

The evaluator MUST score ANSWER, RETRIEVE_MORE, and ABSTAIN against explicit answerability labels only when gold labels are human verified.

#### Scenario: Unverified answerability candidate set

- **WHEN** candidate labels are not human verified
- **THEN** final answerability and abstention metrics are N/A
- **AND** candidate counts and provenance remain available for review

