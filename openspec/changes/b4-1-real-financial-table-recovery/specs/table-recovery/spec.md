# Table recovery

## ADDED Requirements

### Requirement: Preserve real PDF table geometry
The system MUST convert positioned words from the scoped public HSBC PDF pages into TableIR cells with stable document, page, table, row, column, and optional bounding-box provenance.

#### Scenario: Recover a numeric table
- **WHEN** a real HSBC page contains a table-like region with right-aligned numeric columns
- **THEN** the extractor MUST preserve row grouping and deterministic column assignment in the emitted TableIR
- **AND** the run MUST retain the source PDF SHA256 and page scope.

### Requirement: Report unverified semantics honestly
The system MUST report semantic cell correctness, unit correctness, merged-cell correctness, and footnote correctness as `N/A` unless verified annotations exist.

#### Scenario: No human table gold exists
- **WHEN** the extractor produces geometry and TableIR invariants but no verified cell labels exist
- **THEN** the report MUST NOT present invariants as semantic accuracy.
