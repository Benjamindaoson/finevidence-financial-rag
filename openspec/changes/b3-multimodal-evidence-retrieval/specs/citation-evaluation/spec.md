# Citation evaluation

## ADDED Requirements

### Requirement: page citation metrics
When page-level gold exists, the evaluator SHALL report page precision, recall, and F1. Bbox metrics require bbox gold.

#### Scenario: page-only citation
- **WHEN** a predicted page matches page-level gold
- **THEN** page precision/recall/F1 are evaluated without inferring a region match.
