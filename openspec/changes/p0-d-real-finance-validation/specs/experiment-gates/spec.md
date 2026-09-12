## ADDED Requirements

### Requirement: Real-finance results remain separate from controlled fixtures
The runner SHALL label results as `controlled_fixture`, `public_benchmark_slice`, or `hsbc_stress_set` and SHALL not combine their denominators.

#### Scenario: Public and controlled rows are reported
- **WHEN** the runner evaluates RealFinance-v1 and an existing controlled fixture
- **THEN** the output SHALL contain separate labeled rows and separate denominators

### Requirement: HSBC stress data is gated
The runner SHALL emit `N/A` with a machine-readable reason when no locally available, provenance-bearing HSBC corpus exists.

#### Scenario: HSBC corpus is absent
- **WHEN** no eligible local HSBC source corpus is found
- **THEN** the runner SHALL emit `status=N/A` and a reason such as `LOCAL_PROVENANCE_SOURCE_MISSING`

### Requirement: Full FinRAGBench-V is not downloaded
The P0-D workflow SHALL use TAT-QA and FinQA first and SHALL not download the full FinRAGBench-V corpus.

#### Scenario: P0-D acquisition runs
- **WHEN** the P0-D source audit and slice builder execute
- **THEN** they SHALL access only the configured TAT-QA and FinQA source files and SHALL not create a FinRAGBench-V full-corpus download
