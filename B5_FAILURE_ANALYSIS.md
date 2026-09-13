# B5 Failure Analysis

## Observed blocker

The first B5.1 model adapter did not silently fall back to the existing TF-IDF
retriever. It recorded `status=N/A` because the requested Qwen revision was
not locally runnable. This is a model acquisition/runtime failure, not a
retrieval-quality result.

## What remains unmeasured

- neural entity/metric/period/basis hard-negative recovery;
- neural reranking versus deterministic financial facets;
- independent late-interaction recovery;
- modern visual recovery and visual regression;
- agentic coverage gain per budget;
- graph-specific cross-document recovery.

## Existing baseline signal

On the frozen RealFinance-v1 slice, the current hybrid baseline is stronger
than the current dense baseline at R@1, R@5, R@10, MRR, nDCG@10, and complete
evidence rate in this run. This is a baseline observation, not evidence that
the current implementation is optimal.

## Attribution rule

Future B5 failures will be attributed separately to model loading, candidate
recall, hard-negative ranking, evidence alignment, critical coverage, or
controller budget/stop logic. A retrieved page or candidate will never be
counted as qualified evidence without passing the existing gate.
