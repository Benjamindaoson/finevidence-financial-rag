# Table IR

## ADDED Requirements

### Requirement: Preserve available table relations
The Table IR MUST represent table, row, column, and cell identity and MUST preserve source cell order and raw values.

#### Scenario: TAT-QA source table
- **WHEN** a source table array is parsed
- **THEN** every source cell has a stable cell ID, row/column coordinates, provenance, and a round-trip value invariant.

### Requirement: Honest unavailable relations
The Table IR MUST keep caption, footnote, and bbox as nullable when the source does not provide them and MUST NOT infer verified geometry from flattened text.

#### Scenario: Missing geometry
- **WHEN** the source has no cell coordinates or bbox
- **THEN** the output reports those fields as unavailable rather than fabricating them.
