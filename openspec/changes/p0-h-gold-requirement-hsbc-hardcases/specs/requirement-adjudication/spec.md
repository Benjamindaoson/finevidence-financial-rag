# Requirement adjudication

## ADDED Requirements

### Requirement: model-assisted adjudication is not human gold
The annotation dataset MUST be named `RequirementAdjudicated-v1`, record `annotation_method=dual_pass_model_assisted_adjudication`, and record `human_verified=false`.

#### Scenario: provenance is inspectable
- **WHEN** an annotation file is loaded
- **THEN** each case identifies the source case, source dataset, source manifest hash, pass outputs, disagreement and adjudicated output
