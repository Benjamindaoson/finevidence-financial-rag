# Conditional routing

## ADDED Requirements

### Requirement: coverage-aware route
The router SHALL select TEXT, TABLE, VISUAL, MIXED, or UNKNOWN from the question, predicted requirement type, parser signals, and text coverage; it SHALL not read gold modality labels.

#### Scenario: plain text query
- **WHEN** text evidence is sufficient and no visual cue exists
- **THEN** the route is TEXT and visual retrieval is not invoked.
