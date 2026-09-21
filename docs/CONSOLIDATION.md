# FinEvidence consolidation

## Decision

FinEvidence is the single canonical financial RAG project.

The consolidation uses `finevidence-financial-rag` as the architecture and
benchmark base and incorporates only reusable RAG capabilities from
`financial-asset-qa-system`.

## Included capabilities

### From finevidence-financial-rag

- typed Evidence contracts and provenance;
- requirement graphs and fact-evidence alignment;
- evidence coverage / answer-eligibility gates;
- targeted retrieval and failure-aware routing;
- TableIR and table recovery experiments;
- financial facets and hard-negative evaluation;
- retrieval/evidence evaluation harnesses and frozen benchmark manifests.

### Incorporated from financial-asset-qa-system

The consolidation ports the design intent, not the product shell:

- structure-aware chunking;
- table-atomic chunking;
- BM25 lexical retrieval;
- reciprocal-rank fusion;
- Cross-Encoder reranking as an optional backend.

## Explicitly excluded

The following product-specific capabilities are intentionally not part of
FinEvidence:

- stock-price dashboards and frontend product UI;
- RSI, MACD, Bollinger Bands, and trading-oriented analytics;
- market-data provider fallback chains;
- investment-advice workflows;
- unrelated product orchestration and presentation code.

## Canonical RAG lifecycle

1. **Chunking / knowledge organization**
   - structure-aware text chunking;
   - table-atomic evidence;
   - typed financial metadata.

2. **Retrieval**
   - dense retrieval;
   - BM25 retrieval;
   - RRF by default;
   - bounded targeted retrieval and failure routing.

3. **Reranking**
   - deterministic financial-facet and hard-negative rerankers;
   - optional Cross-Encoder backend;
   - finance-aware multi-objective ranking with relevance, financial scope,
     provenance, and evidence coverage novelty.

4. **Evaluation**
   - Recall@K / MRR / nDCG;
   - hard-negative error rate;
   - complete evidence rate;
   - fact / critical-fact coverage;
   - answer eligibility and failure analysis.

## Reproducibility note

Historical reports remain evidence for the code revision and experiment setup
that produced them. Retrieval and reranking measurements affected by the v0.2
consolidation must be rerun before being reported as v0.2 results. FinEvidence
does not silently carry old benchmark numbers forward as new results.
