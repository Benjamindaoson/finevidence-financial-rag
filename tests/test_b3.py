from pathlib import Path

from PIL import Image

from finevidence.contracts.b3 import PageImage
from finevidence.contracts.evidence import Evidence
from finevidence.retrieval.fusion import rrf_fusion, weighted_fusion
from finevidence.retrieval.routing import route_query
from finevidence.retrieval.visual import VisualRetriever


class FakeImageEncoder:
    def __init__(self):
        self.image_paths = []

    def encode_images(self, paths):
        import torch
        self.image_paths.extend(paths)
        return torch.tensor([[1.0, 0.0], [0.0, 1.0]])

    def encode_text(self, texts):
        import torch
        return torch.tensor([[1.0, 0.0]])


def test_page_image_contract_and_visual_retriever_consumes_image(tmp_path: Path):
    image_path = tmp_path / "page.png"
    Image.new("RGB", (20, 30), "white").save(image_path)
    page = PageImage(page_image_id="d:p1:image", document_id="d", page=1, image_path=str(image_path), image_sha256="x", width=20, height=30, dpi=72, render_version="test", source_pdf_sha256="y")
    evidence = Evidence.from_content(document_id="d", source_uri="https://example.test/d.pdf", page=1, block_id="image-1", modality="image", text="CET1 ratio", evidence_id=page.page_image_id, image_path=str(image_path), page_image_id=page.page_image_id, render_hash="x", region_type="page")
    second = evidence.model_copy(update={"evidence_id": "d:p2:image", "page": 2})
    encoder = FakeImageEncoder()
    retriever = VisualRetriever(encoder)
    retriever.fit([evidence, second])
    assert retriever.available
    assert encoder.image_paths == [str(image_path), str(image_path)]
    assert retriever.search("CET1", 1)[0].evidence_id == evidence.evidence_id


def test_fusion_normalizes_scores_and_is_deterministic():
    text = [type("R", (), {"evidence_id": "a", "rank": 1, "retrieval_score": 100.0})(), type("R", (), {"evidence_id": "b", "rank": 2, "retrieval_score": 90.0})()]
    visual = [type("R", (), {"evidence_id": "b", "rank": 1, "retrieval_score": 0.2})(), type("R", (), {"evidence_id": "a", "rank": 2, "retrieval_score": 0.1})()]
    assert [x.evidence_id for x in weighted_fusion(text, visual)] == ["a", "b"]
    assert [x.evidence_id for x in rrf_fusion(text, visual)] == ["a", "b"]


def test_conditional_router_does_not_invoke_visual_for_plain_text():
    assert not route_query("What was revenue in 2025?").visual_invoked
    assert route_query("Which chart shows the revenue trend?").visual_invoked
