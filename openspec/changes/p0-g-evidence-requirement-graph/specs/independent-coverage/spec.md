# Independent coverage

## ADDED Requirements

### Requirement: Detect invalid evidence reuse
The system MUST not count one evidence item as independent support for incompatible requirement roles merely because lexical overlap exists.

#### Scenario: Same evidence reused for current value and explanation
- **WHEN** one evidence item is aligned to both roles and the evidence does not explicitly support both
- **THEN** an invalid reuse event is recorded and independent coverage excludes the invalid reuse

### Requirement: Support derived facts without direct chunks
A derived requirement MUST be covered when all critical dependencies are independently covered and its operation is defined.

#### Scenario: Difference derived from two values
- **WHEN** value A and value B have independent direct support
- **THEN** the derived difference is independently covered without a direct evidence ID for the difference
