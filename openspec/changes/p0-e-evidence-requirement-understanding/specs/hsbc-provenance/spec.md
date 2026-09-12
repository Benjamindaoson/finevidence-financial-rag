# HSBC provenance

## ADDED Requirements

### Requirement: Do not redistribute HSBC documents
The repository MUST contain only source URLs, document metadata, hashes, and local artifact paths; it MUST NOT commit HSBC PDFs or extracted document contents.

#### Scenario: User invokes the fetch script
- **WHEN** the user supplies an official-source manifest
- **THEN** the script downloads to an ignored local directory and records URL, SHA-256, timestamp, document type, and reporting period

### Requirement: Missing HSBC corpus is explicit
The evaluation MUST emit `N/A` with a machine-readable reason when the local HSBC corpus is absent.

#### Scenario: No local HSBC documents exist
- **WHEN** P0-E/F is run without fetched local sources
- **THEN** no HSBC hard-negative score is emitted and the readiness artifact says `LOCAL_PROVENANCE_SOURCE_MISSING`
