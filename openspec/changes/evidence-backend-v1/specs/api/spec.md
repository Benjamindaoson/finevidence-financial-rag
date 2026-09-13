# API

## ADDED Requirements

### Requirement: Expose versioned endpoints
The service MUST expose `/api/v1/evidence/search`, `/api/v1/evidence/coverage`, `/api/v1/table/query`, `/api/v1/evidence/verify`, `/api/v1/evidence/{id}/citation`, and `/health`.

#### Scenario: Health check
- **WHEN** a local process calls `GET /health`
- **THEN** it MUST receive a JSON object with `status: "ok"`.

### Requirement: Reject malformed requests
The API MUST validate request schemas and return a standard HTTP 422 response for malformed JSON or missing required fields.

#### Scenario: Missing query
- **WHEN** search receives no query
- **THEN** the request MUST be rejected without invoking retrieval.
