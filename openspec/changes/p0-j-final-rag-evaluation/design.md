# Design

## Scope

P0-J is an evaluation-only layer. It does not add an Agent, serving feature, model, retriever, or benchmark mutation.

## Contracts

The evaluation module exposes three pure functions:

- citation_metrics: claim-level supporting evidence precision/recall/F1, claim support rate, unsupported citation rate, page accuracy, and optional block/cell accuracy.
- table_semantic_metrics: field-level accuracy with null/N/A handling and structural recovery kept separate.
- answerability_metrics: answerability accuracy, abstention precision/recall/F1, false answer rate, false abstention rate, and partial-evidence detection.

All functions use explicit gold/predicted records and do not infer human verification.

## Annotation state machine

candidate_only → human_review_pending → human_verified

Only the final state may provide canonical gold metrics. A candidate artifact may be used for review preparation or contract tests, never as a resume claim.

## Provenance

Every annotation record stores source dataset/case, evidence IDs, document/page/block/cell location where available, annotator metadata, protocol, and human_verified. The final run manifest stores source hashes and code commit.

## Known blocker

No real human annotator is available in this run. The repository contains no pre-existing human-verified annotation for these three tracks. The runner therefore emits candidate artifacts and N/A final metrics rather than fabricating gold.

