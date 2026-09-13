# Human annotation output

The local workbench writes append-only JSONL files here:

```text
citation.jsonl
table.jsonl
answerability.jsonl
```

Each row contains `annotator_id`, `annotation_time`, `annotation_status`,
`human_verified`, `notes` and `protocol_version`. Only the explicit
`Confirm & Save` action writes `annotation_status=VERIFIED` and
`human_verified=true`; drafts, skips and review requests remain false.

Do not edit the candidate queues to promote labels. Reviewers should correct
or confirm the candidate in the workbench and preserve the append-only history.
