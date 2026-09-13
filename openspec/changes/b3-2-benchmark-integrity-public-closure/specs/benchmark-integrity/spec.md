# Benchmark integrity

## ADDED Requirements

### Requirement: Performance-blind stress audit
The system MUST select the VisualStress audit sample using only frozen case metadata and MUST record the selection rule before consulting retrieval results.

#### Scenario: Fixed audit sample
- **WHEN** the audit runs against `HSBCVisualStress-v1`
- **THEN** it selects exactly two cases per category, records the source manifest hash, and emits no performance-derived selection field.

### Requirement: Per-case attribution evidence
The audit MUST retain gold page mapping, source block identity, T0 candidates at @1/@5/@10/@50, overlap facets, and construction provenance.

#### Scenario: Explaining a zero @10 result
- **WHEN** T0 has no gold page at @10
- **THEN** the output distinguishes observed retrieval absence from construction-bias inference and preserves the @50 result.
