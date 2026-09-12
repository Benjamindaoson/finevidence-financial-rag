## ADDED Requirements

### Requirement: Specialized benchmark suites remain immutable per version
The system SHALL store EvidenceCompleteness-v1 and FinanceHardSet-v1 with manifests, hashes, counts, and category labels; a later version SHALL use a new directory and version.

#### Scenario: Verify a suite before running
- **WHEN** all files match the suite manifest
- **THEN** the suite loads and exposes its version and category counts

#### Scenario: Detect an edited suite
- **WHEN** any suite file changes after manifest creation
- **THEN** the experiment stops before retrieval or scoring

### Requirement: Results produce two comparable tables
The experiment runner SHALL output a ranking table with four rankers and a sufficiency table with Top-K, Coverage Gate, and Targeted Retrieval rows, preserving the same manifest and commit metadata.

#### Scenario: Run the sprint experiments
- **WHEN** both suite manifests verify successfully
- **THEN** the run artifacts contain per-query traces and the two requested summary tables

#### Scenario: Visual path is not entered
- **WHEN** the P0-B/P0-C experiment command runs
- **THEN** no visual encoder, B3 result, or visual benchmark is invoked
