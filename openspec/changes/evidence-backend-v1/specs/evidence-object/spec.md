# Evidence Object

## ADDED Requirements

### Requirement: Return stable provenance-bearing objects
The API MUST return a strict versioned EvidenceObject containing identity, provenance, content, financial metadata, structure, and verification fields.

#### Scenario: Search returns a table cell
- **WHEN** a caller searches for an indexed table fact
- **THEN** the response MUST include evidence id, document hash, page, table id, row id, column id, and verification status
- **AND** absent bbox data MUST remain null.

### Requirement: Preserve internal-to-external separation
The API MUST serialize EvidenceObject without requiring callers to understand internal benchmark or retriever classes.

#### Scenario: Internal Evidence model changes
- **WHEN** internal retrieval returns an Evidence object
- **THEN** the API adapter MUST expose the versioned external shape rather than the internal model directly.
