# Typed Search Controller

## ADDED Requirements

### Requirement: bounded typed search
The controller SHALL enforce maximum steps, queries, modality calls, latency,
and cost budgets.

#### Scenario: budget exhausted
- **WHEN** the next action would exceed a configured budget
- **THEN** the controller SHALL stop with `BUDGET_EXHAUSTED`
- **AND** SHALL preserve the action history and current coverage.

### Requirement: evidence-qualified stopping
The controller SHALL stop as answer-eligible only when all critical
requirements are independently satisfied by valid evidence or derivation.

#### Scenario: incomplete evidence
- **WHEN** a critical requirement remains unsupported
- **THEN** the controller SHALL continue within budget or stop as abstain/incomplete
- **AND** SHALL NOT emit an answer-eligible state.
