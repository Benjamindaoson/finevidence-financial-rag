# Citation evaluation

## ADDED Requirements

### Requirement: evaluate page citations honestly
Citation page precision, recall, and F1 SHALL be calculated only against available page-level gold.

#### Scenario: page-only gold
- **WHEN** bbox labels are absent
- **THEN** page citation metrics are reported and bbox metrics remain N/A
