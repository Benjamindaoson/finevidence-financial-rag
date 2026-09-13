# Visual evidence IR

## ADDED Requirements

### Requirement: image provenance
Image evidence SHALL retain existing Evidence identity and SHALL add page-image identity, image path, and render hash. A page-only item SHALL use a null region bbox.

#### Scenario: page-only evidence
- **WHEN** a page has no verified region annotation
- **THEN** its region bbox is null and page citation remains separately reportable.
