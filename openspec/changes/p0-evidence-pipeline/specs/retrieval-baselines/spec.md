## ADDED Requirements

### Requirement: Run comparable retrieval baselines
The runner SHALL execute named baselines B0, B1, B2, and B3 against the same verified evidence corpus and question set, and SHALL include the backend name and configuration in each result.

#### Scenario: Execute CPU baselines
- **WHEN** the default MiniBench is available
- **THEN** one command produces a result record for B0 through B3 with retrieval outputs and status

#### Scenario: Preserve unavailable modality honestly
- **WHEN** B3 lacks a visual adapter or visual evidence
- **THEN** B3 is marked `N/A` with an explicit reason and no fabricated metrics

### Requirement: Retrieval results retain evidence identity
Every returned candidate SHALL reference an Evidence `evidence_id`, rank, retrieval score, and optional rerank score; retrieval SHALL NOT return free-floating text without provenance.

#### Scenario: Candidate is traceable
- **WHEN** a query returns a top-k candidate
- **THEN** the prediction can resolve that candidate to the original Evidence record and its location

### Requirement: Run artifacts are reproducible
The runner SHALL save configuration, verified dataset manifest, predictions, metrics, and failure cases under a unique run directory without overwriting prior runs.

#### Scenario: Repeat a run
- **WHEN** the same config and manifest are run twice
- **THEN** both run directories exist and contain the required artifact files
