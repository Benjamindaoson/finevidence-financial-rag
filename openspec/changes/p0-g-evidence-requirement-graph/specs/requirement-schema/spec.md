# Requirement schema

## ADDED Requirements

### Requirement: Model typed requirements
The system MUST represent retrieved, derived, explanatory, and context requirements with role, financial slots, operation, criticality, dependencies, and acceptable evidence IDs.

#### Scenario: Derived percentage change
- **WHEN** a question asks for a change between two values
- **THEN** the graph represents the two values as retrieved requirements and the change as a derived requirement depending on both

### Requirement: Preserve legacy benchmark compatibility
The new schema MUST NOT require rewriting existing `FactRequirement` or `RealFinance-v1` source data.

#### Scenario: Existing benchmark loads
- **WHEN** a legacy benchmark is loaded
- **THEN** it remains valid and can be adapted into a requirement graph without changing its manifest
