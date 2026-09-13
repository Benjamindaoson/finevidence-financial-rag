# B4 evaluation

## ADDED Requirements

### Requirement: Qualified recovery metrics
The evaluator MUST report independent critical coverage, recovery, regression, net recovery, wrong escalation, invocation, and latency for each routing policy.

#### Scenario: Evidence-qualified action
- **WHEN** an action returns candidates
- **THEN** candidates pass through the existing evidence qualification gate before recovery is counted.

### Requirement: Separate structure and routing evidence
The evaluator MUST separate Table IR structural invariants from HSBC routing metrics and MUST preserve N/A for unobserved relations.

#### Scenario: No verified HSBC tables
- **WHEN** HSBC parsed evidence has no table cells
- **THEN** structured action availability is reported as unavailable and not renamed as Parsed Page Text success.
