# Visual grounding

## ADDED Requirements

### Requirement: honest regions
The system SHALL report page-level citation separately from bbox/region grounding and SHALL return N/A for bbox metrics when bbox gold is absent.

#### Scenario: no bbox gold
- **WHEN** a benchmark has page gold but no verified bounding boxes
- **THEN** page metrics are computed and bbox metrics are N/A.
