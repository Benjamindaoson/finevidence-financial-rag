# Evaluation

## ADDED Requirements

### Requirement: Compare structured and frozen baselines
The evaluator MUST report T0 Text Only, T1 Parsed Page Text, T2 Real Structured Table IR, V0 Visual Only, T2 + Text, and the diagnostic Oracle Table Executor on the frozen HSBC table-failure cases.

#### Scenario: Table failure recovery
- **WHEN** T1 misses a gold page and T2 retrieves it
- **THEN** the run MUST report recovery and critical-recovery rates separately at cutoffs 1, 5, and 10.

### Requirement: Preserve reproducibility evidence
Every formal run MUST save configuration, dataset hashes, model manifest, TableIR records, rankings, failure rows, traces, and latency metrics under a non-overwriting run directory.

#### Scenario: Repeat the same experiment
- **WHEN** the same code, input hashes, and configuration are run again
- **THEN** structural metrics and ranking outputs MUST be comparable without overwriting the prior run.
