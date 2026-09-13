from __future__ import annotations

from collections.abc import Callable, Iterable
import json
from pathlib import Path
from typing import Any

from finevidence.contracts.evidence import Evidence
from finevidence.contracts.evidence_api import EvidenceObject
from finevidence.contracts.requirements import Requirement, RequirementGraph
from finevidence.evidence.alignment import align_requirement_to_evidence, evaluate_independent_coverage
from finevidence.retrieval.hybrid import HybridRetriever


class AuthorizationBoundaryError(PermissionError):
    pass


Authorizer = Callable[[Evidence, dict[str, str]], bool]


class EvidenceService:
    def __init__(self, evidence: Iterable[Evidence] = (), *, document_hashes: dict[str, str] | None = None, authorizer: Authorizer | None = None) -> None:
        self._evidence = list(evidence)
        self._by_id = {item.evidence_id: item for item in self._evidence}
        self._document_hashes = document_hashes or {}
        self._authorizer = authorizer

    @property
    def catalog_size(self) -> int:
        return len(self._evidence)

    def _filtered(self, filters: dict[str, Any] | None = None) -> list[Evidence]:
        filters = {key: value for key, value in (filters or {}).items() if value is not None}
        security = {key: str(filters[key]) for key in ("tenant_id", "user_role") if key in filters}
        if security and self._authorizer is None:
            raise AuthorizationBoundaryError("security filters require a configured authorizer")
        result = []
        for item in self._evidence:
            if any(getattr(item, key, None) != value for key, value in filters.items() if key not in security):
                continue
            if security and not self._authorizer(item, security):
                continue
            result.append(item)
        return result

    def _object(self, evidence: Evidence, *, score: float | None = None, status: str = "RETRIEVED", confidence: float = 0.0) -> EvidenceObject:
        return EvidenceObject.from_evidence(evidence, document_hash=self._document_hashes.get(evidence.document_id), score=score, coverage_status=status, confidence=confidence)

    def search(self, query: str, filters: dict[str, Any] | None = None, top_k: int = 10) -> list[EvidenceObject]:
        candidates = self._filtered(filters)
        if not candidates:
            return []
        retriever = HybridRetriever(); retriever.fit(candidates)
        ranked = retriever.search(query, min(top_k, len(candidates)))
        return [self._object(self._by_id[item.evidence_id], score=item.rerank_score, confidence=max(0.0, min(1.0, float(item.rerank_score or 0.0)))) for item in ranked]

    def _selected(self, evidence_ids: list[str], question: str) -> list[Evidence]:
        if evidence_ids:
            return [self._by_id[item] for item in evidence_ids if item in self._by_id]
        return [self._by_id[item.evidence_id] for item in self.search(question, top_k=20)]

    def coverage(self, question: str, required_claims: list[Requirement], evidence_ids: list[str] | None = None) -> dict[str, Any]:
        graph = RequirementGraph(requirements=required_claims)
        selected = self._selected(evidence_ids or [], question)
        alignments = [align_requirement_to_evidence(requirement, evidence) for requirement in required_claims for evidence in selected]
        result = evaluate_independent_coverage(graph, alignments, {item.evidence_id for item in selected})
        status = "ELIGIBLE" if result.answer_eligible else ("PARTIAL" if result.independent_coverage else "INSUFFICIENT")
        supported_ids = {item.evidence_id for item in alignments if item.support_type != "NO_SUPPORT"}
        objects = [self._object(item, status="SUPPORTED" if item.evidence_id in supported_ids else "RETRIEVED", confidence=1.0 if item.evidence_id in supported_ids else 0.0) for item in selected]
        return {"coverage_score": result.independent_coverage, "independent_coverage": result.independent_coverage, "critical_coverage": result.critical_coverage, "missing_requirements": result.missing_critical_requirements, "status": status, "evidence": objects}

    def verify(self, claim: str, evidence_ids: list[str] | None = None) -> dict[str, Any]:
        requirement = Requirement(requirement_id="claim", description=claim, fact_type="RETRIEVED_FACT", role="claim", criticality="CRITICAL", acceptable_evidence_ids=list(evidence_ids or []), evidence_role="VALUE_SUPPORT")
        result = self.coverage(claim, [requirement], evidence_ids)
        return {"supported": result["status"] == "ELIGIBLE", "coverage_score": result["coverage_score"], "missing_requirements": result["missing_requirements"], "supporting_evidence": result["evidence"] if result["status"] == "ELIGIBLE" else []}

    def table_query(self, *, entity: str | None = None, metric: str | None = None, period: str | None = None, top_k: int = 20) -> list[EvidenceObject]:
        filters = {"entity": entity, "metric": metric, "period": period, "modality": "table"}
        exact = [item for item in self._filtered(filters) if item.modality == "table"]
        if not exact:
            query = " ".join(filter(None, [entity, metric, period])) or "table"
            return [item for item in self.search(query, {"modality": "table"}, top_k)]
        return [self._object(item) for item in exact[:top_k]]

    def citation(self, evidence_id: str) -> EvidenceObject:
        if evidence_id not in self._by_id:
            raise KeyError(evidence_id)
        return self._object(self._by_id[evidence_id], status="UNVERIFIED")

    @classmethod
    def from_local_hsbc(cls, project_root: str | Path) -> "EvidenceService":
        root = Path(project_root)
        render = root / "artifacts/hsbc_page_images/page_render_manifest.json"
        evidence_path = root / "artifacts/hsbc_local_sources/hsbc_evidence.jsonl"
        if not render.exists() or not evidence_path.exists():
            return cls()
        from finevidence.eval.b3 import _load_evidence
        evidence, _ = _load_evidence(json.loads(render.read_text(encoding="utf-8")), evidence_path)
        manifest_path = root / "artifacts/hsbc_local_sources/hsbc_corpus_manifest.json"
        document_hashes = {}
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            document_hashes = {item["document_id"]: item["sha256"] for item in manifest.get("documents", []) if item.get("document_id") and item.get("sha256")}
        return cls(evidence, document_hashes=document_hashes)
