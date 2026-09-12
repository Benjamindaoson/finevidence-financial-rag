# P0-G evaluation

## ADDED Requirements

### Requirement: Separate gold and predicted coverage
The runner MUST report Gold Independent CER, Predicted Independent CER, Self-vs-Gold Coverage Gap, Critical Coverage Gap, and FAER without mixing gold and predicted requirements.

#### Scenario: Predicted self-coverage is inflated
- **WHEN** raw self-coverage exceeds independent coverage
- **THEN** the runner emits `EVIDENCE_REUSE_INFLATION` and reports both values separately

### Requirement: Preserve complete trace artifacts
Each query MUST write requirements, graph, alignments, reuse events, critical missing requirements, targeted queries, final evidence, coverage values, eligibility, warnings, and failure taxonomy.

#### Scenario: Query fails alignment
- **WHEN** a requirement has no valid supporting alignment
- **THEN** the failure case includes the missing requirement, alignment reason, and stable source IDs
