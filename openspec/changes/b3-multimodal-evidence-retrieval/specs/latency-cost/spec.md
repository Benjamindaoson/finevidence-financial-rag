# Latency and cost

## ADDED Requirements

### Requirement: modality cost trace
The evaluator SHALL report P50/P95 latency, visual pages per query, invocation rate, and available CPU/GPU memory telemetry per system.

#### Scenario: CPU-only run
- **WHEN** no CUDA device is available
- **THEN** the run records CPU device and GPU memory as zero/not applicable without inventing GPU timing.
