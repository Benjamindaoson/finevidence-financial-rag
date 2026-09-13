from __future__ import annotations

from fastapi.testclient import TestClient

from finevidence.api.app import create_app
from finevidence.api.service import EvidenceService
from finevidence.contracts.evidence import Evidence


def _catalog() -> tuple[Evidence, Evidence]:
    current = Evidence.from_content(
        document_id="doc-1",
        source_uri="https://example.test/doc-1.pdf",
        page=3,
        block_id="cell-1",
        modality="table",
        text="HSBC CET1 ratio 2025 14.2%",
        evidence_id="doc-1:p3:cell-1",
        table_id="capital",
        row_id="cet1",
        column_id="2025",
        entity="HSBC",
        metric="CET1 ratio",
        period="2025",
        bbox=(10.0, 20.0, 110.0, 60.0),
    )
    prior = Evidence.from_content(
        document_id="doc-1",
        source_uri="https://example.test/doc-1.pdf",
        page=3,
        block_id="cell-2",
        modality="table",
        text="HSBC CET1 ratio 2024 13.8%",
        evidence_id="doc-1:p3:cell-2",
        table_id="capital",
        row_id="cet1",
        column_id="2024",
        entity="HSBC",
        metric="CET1 ratio",
        period="2024",
    )
    return current, prior


def _client() -> tuple[TestClient, Evidence, Evidence]:
    current, prior = _catalog()
    service = EvidenceService([current, prior], document_hashes={"doc-1": "sha256-doc-1"})
    return TestClient(create_app(service)), current, prior


def test_health_and_search_return_versioned_provenance() -> None:
    client, current, _ = _client()

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "catalog_size": 2}

    response = client.post("/api/v1/evidence/search", json={"query": "HSBC CET1 ratio 2025", "top_k": 1})
    assert response.status_code == 200
    payload = response.json()
    assert payload["api_version"] == "v1"
    assert len(payload["evidence"]) == 1
    item = payload["evidence"][0]
    assert item["evidence_id"] == current.evidence_id
    assert item["source_type"] == "table_cell"
    assert item["provenance"]["document_hash"] == "sha256-doc-1"
    assert item["structure"]["table_id"] == "capital"
    assert item["structure"]["bbox"] == [10.0, 20.0, 110.0, 60.0]
    assert item["verification"]["coverage_status"] == "RETRIEVED"


def test_malformed_search_is_rejected() -> None:
    client, _, _ = _client()
    assert client.post("/api/v1/evidence/search", json={}).status_code == 422


def test_coverage_and_verify_use_existing_qualification() -> None:
    client, current, prior = _client()
    requirement = {
        "requirement_id": "r-current",
        "description": "HSBC CET1 ratio 2025",
        "fact_type": "RETRIEVED_FACT",
        "role": "value",
        "entity": "HSBC",
        "metric": "CET1 ratio",
        "period": "2025",
        "criticality": "CRITICAL",
        "acceptable_evidence_ids": [current.evidence_id],
        "evidence_role": "VALUE_SUPPORT",
    }
    coverage = client.post(
        "/api/v1/evidence/coverage",
        json={"question": "What was HSBC CET1 ratio in 2025?", "required_claims": [requirement], "evidence_ids": [current.evidence_id]},
    )
    assert coverage.status_code == 200
    assert coverage.json()["status"] == "ELIGIBLE"
    assert coverage.json()["evidence"][0]["verification"]["coverage_status"] == "SUPPORTED"

    supported = client.post("/api/v1/evidence/verify", json={"claim": "HSBC CET1 ratio 2025", "evidence_ids": [current.evidence_id]})
    assert supported.status_code == 200
    assert supported.json()["supported"] is True

    unsupported = client.post("/api/v1/evidence/verify", json={"claim": "Unrelated liquidity buffer", "evidence_ids": [prior.evidence_id]})
    assert unsupported.status_code == 200
    assert unsupported.json()["supported"] is False
    assert unsupported.json()["supporting_evidence"] == []


def test_table_query_and_citation_preserve_structure() -> None:
    client, current, _ = _client()
    table = client.post("/api/v1/table/query", json={"entity": "HSBC", "metric": "CET1 ratio", "period": "2025"})
    assert table.status_code == 200
    assert table.json()["evidence"][0]["evidence_id"] == current.evidence_id

    citation = client.get(f"/api/v1/evidence/{current.evidence_id}/citation")
    assert citation.status_code == 200
    assert citation.json()["page_number"] == 3
    assert citation.json()["document_hash"] == "sha256-doc-1"
    assert citation.json()["row_id"] == "cet1"
    assert citation.json()["bbox"] == [10.0, 20.0, 110.0, 60.0]
    assert client.get("/api/v1/evidence/missing/citation").status_code == 404


def test_security_filter_fails_closed_without_authorizer() -> None:
    client, _, _ = _client()
    response = client.post(
        "/api/v1/evidence/search",
        json={"query": "CET1", "filters": {"user_role": "analyst"}},
    )
    assert response.status_code == 403


def test_configurable_authorizer_is_applied_before_ranking() -> None:
    current, prior = _catalog()
    service = EvidenceService([current, prior], authorizer=lambda item, security: item.evidence_id == current.evidence_id and security["user_role"] == "analyst")
    client = TestClient(create_app(service))
    response = client.post("/api/v1/evidence/search", json={"query": "CET1", "filters": {"user_role": "analyst"}, "top_k": 10})
    assert response.status_code == 200
    assert [item["evidence_id"] for item in response.json()["evidence"]] == [current.evidence_id]
