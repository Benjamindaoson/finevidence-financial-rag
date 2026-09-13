# Structure fidelity

## ADDED Requirements

### Requirement: preserve structure claims
Tests SHALL cover row order, column alignment, multi-level headers, units, footnotes, cross-page continuity, captions, and multi-column order using source evidence or an explicit N/A.

#### Scenario: parser ceiling
- **WHEN** a parser cannot expose a structural relation
- **THEN** the report records N/A instead of claiming the relation was preserved.
