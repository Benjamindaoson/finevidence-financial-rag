# Structure fidelity

## ADDED Requirements

### Requirement: do not overclaim parsed structure
The parsed page-text adapter SHALL not claim verified cell, row/column, header, unit, footnote, or geometry structure.

#### Scenario: T1 evaluation
- **WHEN** T1 uses pypdf page text without cell identity
- **THEN** its name is Parsed Page Text and verified structured Table IR is N/A
