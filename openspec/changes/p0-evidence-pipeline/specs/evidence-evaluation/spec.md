## ADDED Requirements

### Requirement: Evaluate retrieval and evidence coverage separately
The system SHALL report Recall@K, MRR, and nDCG for retrieval, and SHALL separately report evidence set recall, complete evidence rate, unsupported answer rate, and missing-fact detection.

#### Scenario: Partial evidence is incomplete
- **WHEN** a case requires three evidence items and the retrieved context contains two
- **THEN** evidence set recall is partial, complete evidence rate is false, and the case is not answer-eligible under B2

#### Scenario: All required evidence is present
- **WHEN** every required evidence reference is present in the selected context
- **THEN** the case is complete and B2 may mark it answer-eligible

### Requirement: Evaluate financial hard negatives
The system SHALL calculate Hard-Negative Error Rate as the fraction of hard-negative cases where any designated negative ranks above the designated positive.

#### Scenario: Negative outranks positive
- **WHEN** a temporal, metric, or entity hard negative is ranked above the gold positive
- **THEN** the case is counted as a hard-negative error

#### Scenario: Positive outranks all negatives
- **WHEN** the gold positive ranks above every designated hard negative
- **THEN** the case is counted as correct for hard-negative ranking

### Requirement: Evaluate citation and answerability without hallucinating metrics
The system SHALL report citation identity accuracy and abstention outcomes only when the case has the required gold annotations, and SHALL use `N/A` for unavailable measures.

#### Scenario: Unanswerable query
- **WHEN** a case is marked unanswerable and the system emits abstention
- **THEN** abstention is scored as correct and no unsupported answer claim is counted

#### Scenario: Missing annotation
- **WHEN** a metric needs a gold bbox or cell annotation that the case does not contain
- **THEN** the metric value is `N/A` with a reason rather than zero or a guessed value
