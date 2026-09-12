# Fact evaluation

## ADDED Requirements

### Requirement: Report fact detection and critical recall
The evaluator MUST report Fact Precision, Fact Recall, Critical Fact Recall, and per-slot accuracy separately.

#### Scenario: A prediction omits a critical fact
- **WHEN** a predicted fact set matches non-critical facts but omits a critical gold fact
- **THEN** Fact Recall and Critical Fact Recall both decrease, and the omission is visible in the failure artifact

### Requirement: Report Oracle Gap
The evaluator MUST report `Oracle Gap = CER_gold_facts - CER_predicted_facts` with the source CER rows identified.

#### Scenario: Predicted facts are under-specified
- **WHEN** predicted-fact self-coverage exceeds gold-fact coverage
- **THEN** the runner reports the negative gap and a calibration warning instead of treating it as a gain
