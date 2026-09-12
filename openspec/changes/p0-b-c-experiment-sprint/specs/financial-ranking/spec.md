## ADDED Requirements

### Requirement: Financial facets are explicit
The system SHALL extract and expose entity, metric, period, basis, segment, geography, currency, and period-type facets when recognized, without hiding the vocabulary version.

#### Scenario: Extract a CET1 query
- **WHEN** the query names HSBC Group, CET1 ratio, and 2024
- **THEN** the facet result contains the corresponding entity, metric, and period values

### Requirement: Ranking variants are comparable
Generic, facet-aware, and hard-negative-aware rankers SHALL return the same candidate identity type and SHALL be evaluated with Recall@5, MRR, nDCG@10, and Hard-Negative Error Rate.

#### Scenario: Rank a temporal hard negative
- **WHEN** 2023 and 2024 evidence share the same metric and entity
- **THEN** the ranking trace records both candidates and the positive/negative ordering

### Requirement: Hard-negative training uses fixed pairs
The hard-negative-aware adapter SHALL train only from the declared positive and hard-negative IDs in FinanceHardSet-v1 and SHALL report per-category and overall HN Error.

#### Scenario: Fit on a fixed hard set
- **WHEN** the same manifest and seed are used twice
- **THEN** the ranker weights and per-query ordering are reproducible
