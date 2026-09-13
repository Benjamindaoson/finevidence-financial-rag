# Latency and cost

## ADDED Requirements

### Requirement: separate query and indexing latency
Query component latency and offline image indexing time SHALL be reported separately with P50/P95 where samples exist.

#### Scenario: CPU-only run
- **WHEN** CUDA is unavailable
- **THEN** GPU and monetary cost remain unclaimed rather than fabricated
