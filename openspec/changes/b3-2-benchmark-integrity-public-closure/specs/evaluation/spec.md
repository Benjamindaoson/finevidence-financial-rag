# Evaluation

## ADDED Requirements

### Requirement: Isolated workload reporting
Stress and natural-control rankings MUST have separate counts and metrics, and the report MUST include T0 page recall at @1/@5/@10/@50 where available.

#### Scenario: Natural control comparison
- **WHEN** both datasets are evaluated
- **THEN** the output contains separate `stress` and `natural` sections and does not pool them into a single headline result.
