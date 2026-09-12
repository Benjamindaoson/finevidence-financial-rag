# Experiment gates

## ADDED Requirements

### Requirement: Keep benchmark families separate
P0-E MUST label controlled fixtures, public finance slices, and HSBC readiness artifacts with distinct dataset types and paths.

#### Scenario: Public P0-E run completes
- **WHEN** RealFinance-v1 is evaluated
- **THEN** the metrics identify `public_benchmark_slice` and do not merge controlled fixture rows into the result

### Requirement: Preserve reproducibility
The runner MUST save configuration, source/derived manifest, per-query predictions or traces, metrics, and failure cases in a new non-overwriting run directory.

#### Scenario: The same frozen configuration runs twice
- **WHEN** two runs use the same code commit and manifest
- **THEN** deterministic metric and manifest content can be compared byte-for-byte
