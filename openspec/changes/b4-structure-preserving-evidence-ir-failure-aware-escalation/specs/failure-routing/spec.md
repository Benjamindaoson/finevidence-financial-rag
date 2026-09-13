# Failure-aware routing

## ADDED Requirements

### Requirement: Oracle routing is evaluation-only
The oracle router MAY use a gold failure category only in the E0 evaluation and MUST record that it is not deployable routing.

#### Scenario: Oracle upper bound
- **WHEN** E0 routes a frozen category
- **THEN** it reports the action and qualified recovery separately from predicted routing.

### Requirement: Predicted routing excludes gold
The predicted router MUST use observable question/retrieval/parser signals and MUST NOT receive gold category or gold modality.

#### Scenario: Predicted action
- **WHEN** a critical requirement is missing
- **THEN** the predicted router selects an action from its observable signals and the trace records no gold input.
