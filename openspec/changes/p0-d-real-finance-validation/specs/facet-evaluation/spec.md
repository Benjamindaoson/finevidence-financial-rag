## ADDED Requirements

### Requirement: Facet extraction is scored independently
The evaluator SHALL report per-field Entity, Metric, Period, Segment, Basis, Geography, and Currency extraction accuracy whenever source-derived labels exist.

#### Scenario: Paraphrased financial query is not recognized
- **WHEN** the query uses a financial synonym not covered by the deterministic vocabulary
- **THEN** the facet field SHALL be recorded as missing or incorrect
- **AND** the ranking result SHALL be attributed to predicted-facet condition rather than gold-facet condition

### Requirement: Ranking conditions are named
The experiment SHALL report facet-aware ranking separately under gold facets and predicted facets, alongside Dense and Hybrid+Generic baselines.

#### Scenario: Gold and predicted facet conditions are compared
- **WHEN** ranking is evaluated on a real-finance case with source-derived facet labels
- **THEN** the output SHALL identify whether facets were gold or predicted and SHALL report the ranking metrics separately
