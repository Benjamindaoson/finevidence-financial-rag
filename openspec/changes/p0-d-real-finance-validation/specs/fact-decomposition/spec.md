## ADDED Requirements

### Requirement: Gold and predicted required facts are separate
The evaluator SHALL support `gold_facts` as an oracle condition and `predicted_facts` as an independently generated condition; it SHALL never silently substitute one for the other.

#### Scenario: Decomposer omits a required fact
- **WHEN** predicted facts do not cover a gold fact
- **THEN** Required Fact Recall SHALL decrease
- **AND** predicted-fact Evidence Completeness SHALL not receive credit for the omitted fact

### Requirement: Fact decomposition metrics are explicit
The evaluator SHALL report Required Fact Precision, Required Fact Recall, and oracle-versus-predicted Initial/Final Complete Evidence Rate.

#### Scenario: Oracle and predicted facts differ
- **WHEN** the predicted decomposer omits one fact that exists in the gold fact set
- **THEN** the report SHALL show predicted Required Fact Recall below 1.0 and SHALL keep oracle completeness separate from predicted completeness
