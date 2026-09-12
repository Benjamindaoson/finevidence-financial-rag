## ADDED Requirements

### Requirement: MiniBench has explicit required evidence
Every benchmark question SHALL contain a unique `question_id`, `question`, `gold_answer`, `failure_type`, `answerable`, and a non-empty `required_evidence` list when `answerable` is true.

#### Scenario: Load a valid answerable question
- **WHEN** a JSONL question contains required evidence references
- **THEN** the loader returns a typed case with all required fields

#### Scenario: Reject answerable question without evidence
- **WHEN** an answerable question has an empty required evidence list
- **THEN** manifest validation fails before retrieval starts

### Requirement: MiniBench is manifest-verified
The system SHALL record source file SHA-256 hashes, question count, evidence count, and benchmark version in a manifest, and SHALL fail a run when a referenced file hash or count no longer matches.

#### Scenario: Verify unchanged fixture
- **WHEN** the runner loads the same files used to create the manifest
- **THEN** manifest verification succeeds and exposes the recorded counts

#### Scenario: Detect changed fixture
- **WHEN** a source JSONL file changes after the manifest is created
- **THEN** the runner stops before scoring and reports a manifest mismatch

### Requirement: MiniBench distinguishes answerability
The system SHALL retain `answerable` and SHALL represent unanswerable or insufficient cases without inventing a gold evidence reference.

#### Scenario: Load an unanswerable case
- **WHEN** a case is marked `answerable: false` and contains no required evidence
- **THEN** validation succeeds and evaluation can score abstention separately
