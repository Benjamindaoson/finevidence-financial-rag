from __future__ import annotations

from collections import Counter
import math
import re

from finevidence.contracts.evidence import Evidence, RetrievedEvidence


def _tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_.%/-]+|[\u4e00-\u9fff]", text)
    ]


class BM25Retriever:
    """Small dependency-free BM25 implementation for reproducible CPU baselines."""

    backend_name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._evidence: list[Evidence] = []
        self._tokens: list[list[str]] = []
        self._dfs: Counter[str] = Counter()
        self._avgdl = 0.0

    def fit(self, evidence: list[Evidence]) -> None:
        self._evidence = list(evidence)
        self._tokens = [_tokenize(item.text) for item in self._evidence]
        self._dfs = Counter()
        for tokens in self._tokens:
            self._dfs.update(set(tokens))
        self._avgdl = (
            sum(len(tokens) for tokens in self._tokens) / len(self._tokens)
            if self._tokens
            else 0.0
        )

    def search(self, query: str, top_k: int) -> list[RetrievedEvidence]:
        if not self._evidence:
            return []
        query_tokens = _tokenize(query)
        n_docs = len(self._evidence)
        scored: list[tuple[float, Evidence]] = []
        for item, tokens in zip(self._evidence, self._tokens):
            counts = Counter(tokens)
            dl = len(tokens)
            score = 0.0
            for term in query_tokens:
                df = self._dfs.get(term, 0)
                idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                tf = counts.get(term, 0)
                denom = tf + self.k1 * (
                    1 - self.b + self.b * dl / max(self._avgdl, 1e-9)
                )
                if tf:
                    score += idf * (tf * (self.k1 + 1)) / denom
            scored.append((score, item))
        scored.sort(key=lambda pair: (-pair[0], pair[1].evidence_id))
        return [
            RetrievedEvidence(
                evidence_id=item.evidence_id,
                rank=rank,
                retrieval_score=float(score),
            )
            for rank, (score, item) in enumerate(scored[:top_k], start=1)
        ]
