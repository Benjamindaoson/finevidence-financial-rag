# HSBC natural hard cases

## Requirements

### Requirement: candidates MUST come from parsed HSBC blocks
Each hard case MUST contain a real positive and at least one real high-similarity negative, each linked to document, page, block/table and source hash, with at least one evidence-backed facet conflict.

#### Scenario: incomplete hard case
- **WHEN** a mined case lacks a positive, a negative, or a verified facet conflict
- **THEN** it is dropped rather than promoted to `HSBCNaturalHard-v1`
