# Visual retrieval

## ADDED Requirements

### Requirement: consume rendered images
The evaluator SHALL use an image encoder that consumes rendered page images; parsed text SHALL NOT be described as visual retrieval.

#### Scenario: visual query
- **WHEN** a visual baseline ranks pages
- **THEN** its encoder input includes the page image path
