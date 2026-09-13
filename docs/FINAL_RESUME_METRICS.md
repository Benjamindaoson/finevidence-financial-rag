# Resume-safe FinEvidence metrics

P0-J created evaluation contracts and candidate queues, but produced no new
formal quality score because no annotation row is `human_verified=true`.

The review workbench is available at
`http://127.0.0.1:8765/review` when the local API is running. Its 50 citation,
24 table and balanced 60-case answerability queues are review inputs only.

1. RealFinance-v1 Hybrid Recall@5: **0.1417** on a fixed 100-case slice
   (50 TAT-QA + 50 FinQA).
2. RealFinance-v1 Hybrid complete evidence rate: **0.0500**.
3. Gold-fact targeted retrieval Final CER: **0.8900**, with FAER **0.0000**.
4. P0-G D3 raw self-coverage: **1.0000**, but independent CER **0.7283**.
5. P0-G D3 invalid evidence reuse rate: **0.4100**.
6. HSBCNaturalHard deterministic facet-aware HN Error: **0.0339** on 59
   project-created, model-assisted-adjudicated cases.
7. B4.1 TableIR structure recoverability: **0.7418** on 24 HSBC regions;
   semantic cell/header/unit/footnote accuracy remains **N/A**.
8. HSBCNaturalMultimodal T1 Parsed Page Text Recall@10: **0.5875** on 80
   real HSBC pages; this is not verified Structured Table IR.

Do not state P0-J citation F1, claim support rate, table semantic accuracy,
answer accuracy, unsupported claim rate or abstention F1. Those are `N/A`
until real human verification is completed.
