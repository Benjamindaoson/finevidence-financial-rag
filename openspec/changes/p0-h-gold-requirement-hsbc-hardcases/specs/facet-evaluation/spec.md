# Facet evaluation

## ADDED Requirements

### Requirement: predicted and adjudicated facets MUST be separated
Facet extraction metrics MUST be computed against adjudicated facet labels only where a label exists, and predicted-facet ranking MUST be reported separately from adjudicated-facet ranking.

#### Scenario: missing slot label
- **WHEN** a case has no reliable adjudicated value for a slot
- **THEN** that slot metric is `N/A` and is excluded from its denominator
