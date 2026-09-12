# Design

## Structured fact contract

`FactSlots` is a small Pydantic model with nullable entity/metric/period/segment/basis values, a required `fact_type` and `role`, and a `critical` boolean. A fact prediction carries its slots and optional evidence IDs. Existing `FactRequirement` remains backward compatible.

## Decomposer variants

- D0 wraps the existing deterministic splitter as the frozen baseline.
- D1 is a provider boundary. It returns `N/A` when no explicitly authorized LLM provider and frozen prompt/seed are configured; it must not silently substitute a heuristic.
- D2 classifies the question and instantiates a fixed template for factual, comparison, numerical, explanation, trend, and multi-document synthesis questions.
- D3 uses the same schema templates plus candidate evidence text to retain only facts with an evidence-bearing candidate. It is a deterministic adapter, not an agent loop.

## Evaluation

Gold evidence refs remain the controlling evidence target. Structured slot metrics are reported only for cases carrying structured gold slots; absent labels are `N/A`. Lexical fact detection is retained as a diagnostic, not promoted to a semantic gold claim. Oracle Gap is `CER_gold_facts - CER_predicted_facts`; a negative value is reported as a calibration warning rather than an improvement claim.

## HSBC provenance track

The fetch script accepts a checked-in manifest of official HSBC URLs and downloads only on user invocation. It writes SHA-256 and retrieval timestamp to a local manifest and never writes PDFs into Git. Without a local downloaded corpus, HSBC case generation and stress metrics remain `N/A`.
