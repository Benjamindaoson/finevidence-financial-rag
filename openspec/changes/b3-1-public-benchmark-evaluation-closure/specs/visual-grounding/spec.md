# Visual grounding

## ADDED Requirements

### Requirement: separate page and region grounding
Page-level hits SHALL remain distinct from region or bounding-box grounding.

#### Scenario: no bbox gold
- **WHEN** a benchmark has page-level labels only
- **THEN** bbox metrics are reported as N/A
