# Requirement matching

## Requirements

### Requirement: requirement scoring MUST be one-to-one
Predicted and adjudicated requirements MUST be matched by a one-to-one assignment using structured compatibility plus description similarity; one requirement MUST NOT match multiple requirements on either side.

#### Scenario: duplicate candidate matches
- **WHEN** two predicted requirements prefer the same adjudicated requirement
- **THEN** only one is matched and the other is recorded as unmatched
