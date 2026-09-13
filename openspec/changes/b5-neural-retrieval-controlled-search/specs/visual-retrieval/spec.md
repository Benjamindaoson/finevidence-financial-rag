# Visual Retrieval

## ADDED Requirements

### Requirement: visual retrieval consumes images
The visual retriever SHALL rank rendered page images using an image-consuming
model and SHALL retain page-image provenance.

#### Scenario: text-only fallback
- **WHEN** no image-consuming model is available
- **THEN** the visual variant SHALL be `N/A`
- **AND** OCR/text retrieval SHALL NOT be reported as visual retrieval.

### Requirement: qualification is mandatory
Visual candidates SHALL pass alignment, reuse policy, independent coverage,
and critical coverage before they can satisfy a requirement.

#### Scenario: visual page hit
- **WHEN** a visual candidate is returned
- **THEN** the candidate SHALL remain only retrieved evidence until qualification passes
- **AND** a page hit alone SHALL NOT mark a critical requirement complete.
