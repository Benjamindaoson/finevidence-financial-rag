# Fact understanding

## ADDED Requirements

### Requirement: Preserve structured fact slots
The system MUST represent a required fact with `fact_type`, `entity`, `metric`, `period`, `segment`, `basis`, `role`, and `critical`, while preserving the existing free-text description and acceptable evidence IDs.

#### Scenario: Existing benchmark remains loadable
- **WHEN** a legacy `MiniCase` is loaded without structured slots
- **THEN** the case loads without migration failure and structured metrics report unavailable labels as `N/A`

### Requirement: Compare decomposer levels
The P0-E runner MUST emit separate rows for D0 Heuristic, D1 LLM Direct, D2 Schema-constrained, and D3 Evidence-aware decomposition.

#### Scenario: LLM provider is not configured
- **WHEN** P0-E runs without an explicitly authorized LLM provider
- **THEN** D1 is `N/A` with a machine-readable reason and no heuristic result is labeled D1

### Requirement: Evidence-aware prediction is bounded
D3 MUST consume only the supplied question and candidate evidence, MUST NOT call an agent loop, and MUST preserve the candidate evidence IDs used for each prediction.

#### Scenario: Candidate evidence is incomplete
- **WHEN** a required fact has no candidate evidence match
- **THEN** D3 retains the missing fact as unresolved instead of inventing supporting evidence
