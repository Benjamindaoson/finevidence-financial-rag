# B5 Evaluation

## ADDED Requirements

#### Scenario: fresh run directory
- **WHEN** a B5 experiment starts
- **THEN** it SHALL write a new run directory
- **AND** SHALL preserve historical artifact directories.

### Requirement: stage-level ablation
Each B5 intervention SHALL report retrieval, evidence qualification,
hard-negative, failure-recovery, and system-cost metrics where applicable.

#### Scenario: completed stage
- **WHEN** an intervention is runnable
- **THEN** the stage output SHALL include its applicable metrics and per-case rows
- **AND** it SHALL record unobserved metrics as `N/A`.

### Requirement: historical preservation
The B5 runner SHALL write to a new run directory and SHALL not overwrite
historical experiment outputs or mutate frozen benchmark files.

#### Scenario: existing result directory
- **WHEN** the configured artifact directory already contains prior runs
- **THEN** the runner SHALL allocate a distinct run ID
- **AND** SHALL leave prior result files byte-for-byte unchanged.
