# Neural Retrieval

## ADDED Requirements

### Requirement: model-backed adapters are explicit
The system SHALL expose model-backed retrieval through an adapter that records
model name, revision/hash when available, runtime, device, and status.

#### Scenario: unavailable model
- **WHEN** a checkpoint cannot be loaded or executed
- **THEN** the experiment SHALL record `N/A` and the technical reason
- **AND** SHALL NOT label a heuristic result as the unavailable model.

### Requirement: frozen comparison
All retrieval variants in one comparison SHALL use the same query set, corpus,
qrels, candidate policy, and metric definitions.

#### Scenario: ablation comparison
- **WHEN** two retrieval variants are compared
- **THEN** their dataset manifest and metric configuration SHALL match
- **AND** any representation change SHALL be recorded explicitly.
