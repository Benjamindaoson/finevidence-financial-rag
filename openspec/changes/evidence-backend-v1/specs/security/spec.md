# Security boundary

## ADDED Requirements

### Requirement: Fail closed for unsupported security filters
The service MUST provide a filter/authorization boundary and MUST NOT imply ACL enforcement when the configured catalog cannot enforce a requested security filter.

#### Scenario: Caller supplies a role filter without an authorizer
- **WHEN** search includes a security filter and no authorizer is configured
- **THEN** the service MUST return a clear authorization error rather than returning unfiltered evidence.
