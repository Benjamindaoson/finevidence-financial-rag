# HSBC corpus provenance

## Requirements

### Requirement: downloaded HSBC documents MUST be reproducible
Every local HSBC document MUST record document ID, official URL, download time, SHA-256, file size, page count, document type, reporting period, issuer, language and ignored local artifact path.

#### Scenario: source file changes
- **WHEN** the local file hash differs from the manifest
- **THEN** the corpus is invalid and ranking evaluation MUST stop
