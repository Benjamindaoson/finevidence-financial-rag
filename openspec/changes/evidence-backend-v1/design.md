# Design

## Contract adapter

`EvidenceObject` is the only external evidence representation. It separates identity, provenance, content, financial metadata, structure, and verification. It keeps optional fields explicit rather than flattening table cells or visual references into untraceable text.

## Service

`EvidenceService` owns a catalog and indexes it with the existing CPU `HybridRetriever`. Table queries use exact normalized metadata first and return table evidence; they do not synthesize missing facts. Search filters are applied before ranking. An authorization hook is injectable and defaults to allow only when no security filter is requested.

Coverage accepts a question plus serialized `Requirement` objects, invokes existing alignment and independent coverage, and returns missing critical requirements. Verify evaluates one claim against supplied evidence ids or the catalog search result. Citation is a pure provenance projection from a known evidence id.

## Runtime

FastAPI routes are thin request/response adapters. The default app loads the ignored local HSBC page catalog when its provenance, render, and evidence artifacts are present; otherwise it constructs an empty service so `/health` and contract behavior remain runnable without private data. Deployments and tests can call `configure_default_service` with a local catalog. Docker packages the API but does not copy PDFs or model weights.

## Compatibility

Existing `Evidence`, retrievers, B3/B4 runners, configs, benchmark manifests, and artifact directories are unchanged. The new API contract is additive.
