# Multimodal fusion

## ADDED Requirements

### Requirement: normalize modality scores
Fusion SHALL use rank fusion or normalized scores; raw scores from different retrievers SHALL NOT be added without normalization.

#### Scenario: weighted fusion
- **WHEN** text and visual scores have different scales
- **THEN** the fusion path normalizes them before weighting
