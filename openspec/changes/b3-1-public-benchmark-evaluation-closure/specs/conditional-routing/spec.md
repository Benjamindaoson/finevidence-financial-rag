# Conditional routing

## ADDED Requirements

### Requirement: keep route labels evaluation-only
The routing evaluation SHALL use balanced real-page classes and SHALL keep gold modality labels out of routing inputs.

#### Scenario: mixed routing evaluation
- **WHEN** a routing case is evaluated
- **THEN** the router receives question and observed coverage, while gold route is read only by the metric calculator
