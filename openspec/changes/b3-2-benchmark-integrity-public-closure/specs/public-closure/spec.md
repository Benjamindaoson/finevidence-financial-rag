# Public closure

## ADDED Requirements

### Requirement: Revision-pinned public data
The public evaluator MUST use the frozen FinRAGBench-V revision and slice manifests without changing query, qrel, or slice selection.

#### Scenario: Download blocked
- **WHEN** the official archive remains unavailable after a documented alternate transport attempt
- **THEN** the archive identity and full blocker evidence are retained and page-image metrics remain N/A.

### Requirement: Verified public evaluation
The evaluator MUST report T0, T1 Parsed Page Text, V0, M0, and M1 only after archive identity and required page files are verified.

#### Scenario: Public archive verified
- **WHEN** the required slice pages are present and hash/provenance checks pass
- **THEN** the existing evaluator runs the five frozen systems without rewriting the slice.
