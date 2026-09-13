from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from .schemas import CitationResponse, CoverageRequest, CoverageResponse, HealthResponse, SearchRequest, SearchResponse, TableQueryRequest, TableQueryResponse, VerifyRequest, VerifyResponse
from .service import AuthorizationBoundaryError, EvidenceService
from .review import ReviewStore, create_review_router


def create_app(service: EvidenceService | None = None, review_root: Path | None = None) -> FastAPI:
    api = FastAPI(title="FinEvidence Evidence Backend", version="1.0.0")
    api.state.evidence_service = service or EvidenceService.from_local_hsbc(Path(__file__).resolve().parents[3])
    api.include_router(create_review_router(ReviewStore(review_root or Path(__file__).resolve().parents[3])))

    @api.get("/health", response_model=HealthResponse)
    def health() -> dict:
        return {"status": "ok", "catalog_size": api.state.evidence_service.catalog_size}

    @api.post("/api/v1/evidence/search", response_model=SearchResponse)
    def search(request: SearchRequest) -> dict:
        try:
            evidence = api.state.evidence_service.search(request.query, request.filters.model_dump(exclude_none=True), request.top_k)
        except AuthorizationBoundaryError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return {"evidence": evidence, "catalog_size": api.state.evidence_service.catalog_size}

    @api.post("/api/v1/evidence/coverage", response_model=CoverageResponse)
    def coverage(request: CoverageRequest) -> dict:
        return api.state.evidence_service.coverage(request.question, request.required_claims, request.evidence_ids)

    @api.post("/api/v1/table/query", response_model=TableQueryResponse)
    def table_query(request: TableQueryRequest) -> dict:
        try:
            return {"evidence": api.state.evidence_service.table_query(entity=request.entity, metric=request.metric, period=request.period, top_k=request.top_k)}
        except AuthorizationBoundaryError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @api.post("/api/v1/evidence/verify", response_model=VerifyResponse)
    def verify(request: VerifyRequest) -> dict:
        return api.state.evidence_service.verify(request.claim, request.evidence_ids)

    @api.get("/api/v1/evidence/{evidence_id}/citation", response_model=CitationResponse)
    def citation(evidence_id: str) -> dict:
        try:
            evidence = api.state.evidence_service.citation(evidence_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="evidence not found") from exc
        return {"evidence_id": evidence.evidence_id, "document_id": evidence.document_id, "document_name": evidence.provenance.document_name, "page_number": evidence.provenance.page_number, "source_url": evidence.provenance.source_url, "document_hash": evidence.provenance.document_hash, "table_id": evidence.structure.table_id, "row_id": evidence.structure.row_id, "column_id": evidence.structure.column_id, "bbox": evidence.structure.bbox}

    return api


app = create_app()


def configure_default_service(service: EvidenceService) -> None:
    """Replace the process-local service for embedding or integration tests."""
    app.state.evidence_service = service
