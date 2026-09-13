# Page rendering

## ADDED Requirements

### Requirement: deterministic page images
The system SHALL render each selected PDF page with fixed DPI and renderer version and SHALL record source PDF hash, page, output path, image hash, dimensions, and render version.

#### Scenario: repeat render
- **WHEN** the same PDF page is rendered twice with the same configuration
- **THEN** the image hash and dimensions are identical.
