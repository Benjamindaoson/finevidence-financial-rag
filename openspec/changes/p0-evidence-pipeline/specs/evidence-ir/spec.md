## ADDED Requirements

### Requirement: Evidence records are location-addressable
The system SHALL represent each evidence item with a stable `evidence_id`, `document_id`, `source_uri`, `page`, `block_id`, `modality`, `text`, and `content_hash`; optional `bbox`, `table_id`, `row_id`, and `column_id` SHALL be nullable rather than omitted from the serialized contract.

#### Scenario: Serialize a text evidence item
- **WHEN** a text block is converted into Evidence
- **THEN** JSON serialization contains its stable identity, page/block location, modality, text, and SHA-256 content hash

#### Scenario: Serialize a table-cell evidence item
- **WHEN** a table cell is converted into Evidence
- **THEN** JSON serialization preserves document/page/block plus table, row, column, and optional bounding-box identity

### Requirement: Evidence identity is content-addressed
The system SHALL compute the same `content_hash` for the same normalized content and SHALL reject an Evidence record whose supplied hash does not match its normalized content.

#### Scenario: Hash is reproducible
- **WHEN** identical normalized text is hashed twice
- **THEN** both Evidence records contain the same SHA-256 hash

#### Scenario: Hash mismatch is rejected
- **WHEN** a caller supplies a hash different from the normalized content hash
- **THEN** Evidence validation fails with a field-specific error

### Requirement: Evidence preserves provenance and scores
The system SHALL preserve `entity`, `metric`, `period`, `retrieval_score`, and `rerank_score` fields when present, without using missing values as implicit evidence.

#### Scenario: Round-trip provenance
- **WHEN** an Evidence record with financial metadata and retrieval scores is serialized and loaded
- **THEN** all metadata and scores round-trip without loss
