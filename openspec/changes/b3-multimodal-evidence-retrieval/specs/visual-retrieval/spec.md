# Visual retrieval

## ADDED Requirements

### Requirement: image-consuming retrieval
The visual retriever SHALL encode image bytes through a configured image model and SHALL rank page-image evidence by query-image compatibility. OCR text embedding alone SHALL not qualify as visual retrieval.

#### Scenario: real image encoder
- **WHEN** visual retrieval is enabled
- **THEN** image paths are passed to the configured image encoder before ranking.
