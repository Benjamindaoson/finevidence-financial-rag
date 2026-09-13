# Multimodal fusion

## ADDED Requirements

### Requirement: normalized fusion
Fusion SHALL normalize modality scores before weighted combination and SHALL support deterministic RRF.

#### Scenario: incompatible score scales
- **WHEN** text and visual scores have different ranges
- **THEN** fusion normalizes each modality before weighted combination.
