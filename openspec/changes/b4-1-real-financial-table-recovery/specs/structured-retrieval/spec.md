# Structured retrieval

## ADDED Requirements

### Requirement: Execute over TableIR cells
The structured retriever MUST rank cell evidence containing table identity, row identity, column identity, header context, and value context; it MUST NOT be a renamed page-text retriever.

#### Scenario: Query a table value
- **WHEN** a query is evaluated by T2
- **THEN** the returned Evidence MUST have modality `table` and preserve table, row, column, page, and geometry metadata.

### Requirement: Qualify structured evidence
T2 candidates MUST pass the existing fact-evidence alignment and independent critical coverage gate before being counted as qualified evidence.

#### Scenario: Relevant page but unsupported cell
- **WHEN** a table cell is on a gold page but does not lexically align with the requirement
- **THEN** it MUST NOT make the requirement eligible solely because of page membership.
