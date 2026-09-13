import json

import pytest
from fastapi.testclient import TestClient

from finevidence.api.app import create_app
from finevidence.api.review import ReviewStore, ReviewSubmission
from finevidence.api.service import EvidenceService


def _review_root(tmp_path):
    candidates = tmp_path / "artifacts" / "final_rag_eval" / "candidates"
    candidates.mkdir(parents=True)
    (candidates / "claim_citation_candidates.jsonl").write_text(
        json.dumps({"case_id": "case:1", "claim": "claim", "supporting_evidence_ids": ["e1"]}) + "\n",
        encoding="utf-8",
    )
    (candidates / "table_semantic_candidates.jsonl").write_text(
        json.dumps({"table_id": "table:1", "cells": []}) + "\n", encoding="utf-8"
    )
    (candidates / "answerability_candidates.jsonl").write_text(
        json.dumps({"case_id": "answer:1", "available_evidence_ids": [], "missing_evidence_ids": []}) + "\n", encoding="utf-8"
    )
    evidence = tmp_path / "benchmarks" / "real_finance_v1"
    evidence.mkdir(parents=True)
    (evidence / "evidence.jsonl").write_text(
        json.dumps({"evidence_id": "e1", "text": "source", "page": 2}) + "\n",
        encoding="utf-8",
    )
    return tmp_path


def test_review_store_only_promotes_on_verified(tmp_path):
    root = _review_root(tmp_path)
    store = ReviewStore(root)
    assert store.queue("citation")[0]["evidence"][0]["text"] == "source"
    draft = store.save("citation", "case:1", ReviewSubmission(annotator_id="u1", annotation_status="DRAFT"))
    assert draft["human_verified"] is False
    verified = store.save(
        "citation",
        "case:1",
        ReviewSubmission(
            annotator_id="u1",
            annotation_status="VERIFIED",
            support_status="SUPPORTED",
            gold_supporting_evidence_ids=["e1"],
        ),
    )
    assert verified["human_verified"] is True
    rows = (root / "artifacts" / "final_rag_eval" / "human_annotations" / "citation.jsonl").read_text()
    assert rows.count("\n") == 2


def test_verified_review_requires_track_label(tmp_path):
    root = _review_root(tmp_path)
    with pytest.raises(ValueError, match="VERIFIED_REQUIRES_TRACK_LABEL"):
        ReviewStore(root).save("citation", "case:1", ReviewSubmission(annotator_id="u1", annotation_status="VERIFIED"))
    with pytest.raises(ValueError, match="VERIFIED_REQUIRES_TRACK_LABEL"):
        ReviewStore(root).save(
            "answerability",
            "answer:1",
            ReviewSubmission(annotator_id="u1", annotation_status="VERIFIED", answerability="UNANSWERABLE"),
        )


def test_review_page_and_queue_are_local_api_routes(tmp_path):
    root = _review_root(tmp_path)
    client = TestClient(create_app(EvidenceService(), review_root=root))
    assert client.get("/review").status_code == 200
    response = client.get("/api/v1/review/queue?track=citation")
    assert response.status_code == 200
    assert response.json()[0]["case_id"] == "case:1"
    table = client.get("/api/v1/review/queue?track=table")
    assert table.status_code == 200
    assert table.json()[0]["case_id"] == "table:1"
