# B5 Decisions

## Decisions from the first increment

| Component | Decision | Reason |
|---|---|---|
| Current TF-IDF/SVD dense | KEEP_AS_OPTIONAL | Frozen, reproducible CPU baseline |
| Current hybrid | KEEP_AS_OPTIONAL | Stronger than current dense on B5.1 frozen slice |
| Qwen3 embedding | INCONCLUSIVE | Real checkpoint was not runnable; no quality claim |
| Neural reranker | INCONCLUSIVE | No runnable checkpoint evaluated |
| ColBERT late interaction | INCONCLUSIVE | No real token-level checkpoint/index evaluated |
| ColQwen/ColPali visual | INCONCLUSIVE | No new model evaluated; historical CLIP results remain unchanged |
| Typed controller | KEEP_AS_OPTIONAL | Contract and bounded selection implemented; end-to-end quality gate not yet run |
| Evidence graph | KEEP_AS_OPTIONAL | Typed primitive exists; promotion awaits measured cross-document gain |

## Production candidate

There is no B5 production candidate yet. The evidence-qualified current
baseline remains the only measured candidate. Neural modules must earn
promotion through frozen ablations and executed-model evidence.

## Next justified action

Resolve the model-weight acquisition/runtime blocker or authorize a smaller
already-runnable neural checkpoint, then run B5.1 before adding reranking,
late interaction, visual models, or graph retrieval.
