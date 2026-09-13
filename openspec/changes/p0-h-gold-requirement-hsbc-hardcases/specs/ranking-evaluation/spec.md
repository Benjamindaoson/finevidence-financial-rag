# Ranking evaluation

## ADDED Requirements

### Requirement: financial ranking MUST report category failures
Dense, hybrid, predicted-facet and adjudicated-facet ranking MUST report Recall@5, MRR, nDCG@10, HN Error, Top-1 Positive Rate and per-category HN Error.

#### Scenario: facet extraction versus ranking error
- **WHEN** predicted-facet and adjudicated-facet rankings differ
- **THEN** the runner MUST expose the difference as a ranking oracle gap
