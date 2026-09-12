from __future__ import annotations

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from finevidence.contracts.evidence import Evidence, RetrievedEvidence


class DenseRetriever:
    """CPU dense baseline; backend name is intentionally tfidf_svd_dense, not neural."""

    backend_name = "tfidf_svd_dense"

    def __init__(self) -> None:
        self._evidence: list[Evidence] = []
        self._vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), lowercase=True)
        self._svd: TruncatedSVD | None = None
        self._matrix = None

    def fit(self, evidence: list[Evidence]) -> None:
        self._evidence = list(evidence)
        matrix = self._vectorizer.fit_transform([item.text for item in self._evidence])
        max_components = min(32, matrix.shape[0] - 1, matrix.shape[1] - 1)
        # SVD on a corpus this small can rotate away the only discriminative
        # term; retain the full normalized vector for the development slice.
        if max_components >= 1 and matrix.shape[0] >= 8:
            self._svd = TruncatedSVD(n_components=max_components, random_state=0)
            self._matrix = normalize(self._svd.fit_transform(matrix))
        else:
            self._matrix = normalize(matrix.toarray())

    def search(self, query: str, top_k: int) -> list[RetrievedEvidence]:
        if not self._evidence or self._matrix is None:
            return []
        query_matrix = self._vectorizer.transform([query])
        if self._svd is not None:
            query_vector = normalize(self._svd.transform(query_matrix))
        else:
            query_vector = normalize(query_matrix.toarray())
        scores = (self._matrix @ query_vector.T).ravel()
        order = sorted(range(len(self._evidence)), key=lambda i: (-float(scores[i]), self._evidence[i].evidence_id))
        return [
            RetrievedEvidence(
                evidence_id=self._evidence[index].evidence_id,
                rank=rank,
                retrieval_score=float(scores[index]),
            )
            for rank, index in enumerate(order[:top_k], start=1)
        ]
