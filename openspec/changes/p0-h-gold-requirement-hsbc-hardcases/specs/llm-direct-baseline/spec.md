# LLM direct baseline

## ADDED Requirements

### Requirement: D1 MUST be a real local model or explicit N/A
D1 MUST consume the question and schema instruction without gold evidence or gold requirements. Its config MUST record model, revision/hash, runtime, device, prompt version and generation parameters, or an exact technical N/A reason.

#### Scenario: malformed model output
- **WHEN** D1 emits malformed JSON
- **THEN** the runner performs at most one bounded schema repair attempt and records both raw output and parse status
