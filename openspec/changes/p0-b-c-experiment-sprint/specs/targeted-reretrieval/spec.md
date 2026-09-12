## ADDED Requirements

### Requirement: Missing facts generate targeted queries
The system SHALL construct a query from the original question and each missing fact description, rather than simply repeating the original question.

#### Scenario: Construct a management-explanation query
- **WHEN** the missing fact description is `management explanation for cost of risk change`
- **THEN** the targeted query contains that description and the original question context

### Requirement: Re-retrieval is bounded and traceable
The system SHALL perform no more than two targeted retrieval rounds, merge unique evidence IDs, and record original query, round number, targeted query, retrieved IDs, covered facts, and missing facts for every round.

#### Scenario: One round completes coverage
- **WHEN** the first targeted round retrieves all missing facts
- **THEN** the result is complete and the trace contains the initial plus one targeted round

#### Scenario: Two rounds remain incomplete
- **WHEN** missing facts remain after two targeted rounds
- **THEN** the result is incomplete, no third round runs, and the final trace records the remaining facts
