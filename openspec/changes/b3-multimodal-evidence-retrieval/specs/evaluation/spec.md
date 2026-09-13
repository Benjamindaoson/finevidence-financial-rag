# Evaluation

## ADDED Requirements

### Requirement: recovery and regression
The evaluator SHALL report page Recall@1/5/10, MRR, nDCG@10, text failure recovery, critical requirement recovery, multimodal regression, net recovery, and per-failure-type metrics for T0/T1/V0/M0/M1.

#### Scenario: multimodal regression
- **WHEN** text-only finds gold but a multimodal system loses it
- **THEN** the case is counted as a multimodal regression and retained in failure cases.
