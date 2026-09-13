# Evidence Service

## ADDED Requirements

### Requirement: Search indexed evidence
The service MUST search available text/table/image evidence and return deterministic, provenance-bearing results.

#### Scenario: Empty catalog
- **WHEN** search runs before a catalog is configured
- **THEN** the API MUST return an empty result with a clear catalog status and MUST NOT fabricate evidence.

### Requirement: Verify claims through qualification
The service MUST use existing alignment and independent coverage semantics for coverage and verification responses.

#### Scenario: Unsupported claim
- **WHEN** supplied evidence does not align with a claim
- **THEN** the response MUST mark the claim unsupported and list missing requirements.
