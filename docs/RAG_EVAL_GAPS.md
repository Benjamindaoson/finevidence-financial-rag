# FinEvidence RAG Evaluation Gaps

> 这是一份“缺什么、为什么缺、是否值得补”的测评账，不是下一阶段开发计划。当前任务不实现这些能力，也不重跑冻结实验。

## 优先级定义

- P0：如果没有它，无法把已有结论说成可信的高风险 RAG 能力；适合优先补测。
- P1：能明显提高面试深挖和工程判断的可信度，但不阻塞当前 Evidence Backend v1。
- P2：生产化或规模化重要，但在当前研究边界内不值得立即补。

## P0 gaps

| 缺口 | 为什么重要 | 可复用数据 | 最小实验规模/人工量 | 当前是否值得为了简历补 | 现状 |
|---|---|---|---:|---|---|
| Claim-level citation support | page hit 不证明 claim 被支持；高风险回答必须能证明 claim→evidence→page/block/region | RealFinance-v1、HSBC parsed blocks、Backend citation contract | 30–50 cases；每 case 1–3 claims，人工逐条标注 supporting evidence | 是 | MISSING；Citation P/R/F1、Claim Support Rate 未测 |
| Answerable / unanswerable / partial evidence set | 没有 abstention gold，就不能证明系统知道何时不应回答 | RealFinance-v1 可扩展；RequirementAdjudicated-v1 仅部分覆盖 | 50–100 cases；至少 1/3 unanswerable 或 partial | 是 | MISSING；当前 FAER/eligibility 不是 answer abstention quality |
| Verified table semantic gold | structure invariant=1.0 不等于 cell/header/unit/footnote 正确 | HSBC pages 1–26 的 24 regions；现有 TableIR 输出 | 20–30 tables/regions；逐 cell 或关键 cell 标注 | 是 | N/A；是 B4.1 最大语义缺口 |
| Requirement gold with real human verification | D4=72.22% 受 model-assisted adjudication 与 template ceiling 影响 | RequirementAdjudicated-v1 可作为候选层 | 30–40 cases；至少双人或专家复核 | 有条件 | 当前 human_verified=false；RequirementGold-v1=N/A |

## P1 gaps

| 缺口 | 为什么重要 | 可复用数据 | 最小实验规模/人工量 | 当前是否值得为了简历补 | 现状 |
|---|---|---|---:|---|---|
| Chunk size / overlap ablation | 判断 recall 提升来自检索器还是切分策略 | RealFinance-v1 100 cases | 3 chunk sizes × 2 overlaps；固定 seeds | 是，若面向 RAG 算法岗 | MISSING |
| Page vs block vs cell granularity | 连接 ingestion 选择与 downstream evidence completeness | RealFinance/HSBC；HSBC TableIR 24 regions | 3 granularity conditions；30–50 cases | 是 | MISSING |
| Table detection P/R 与 reading order | 解释 parser failure，而不是只看最终 retrieval | HSBC 494 pages，重点 50–100 pages | 人工 page/region label；约 50–100 pages | 是 | MISSING |
| Failure attribution calibration | 当前 failure taxonomy 有分类，但 predicted router 的分类能力仍只有 route accuracy=0.5000 | HSBCVisualStress-v1、HSBCNaturalMultimodal-v1 | 60–100 cases；双 pass | 可选 | PARTIAL |
| Visual region/bbox grounding | page-level visual hit 不能支持 row/figure/region citation | HSBC page images；现有 bbox fields | 30–50 regions；人工 bbox/region labels | 是，若主打 multimodal | N/A；当前无真实 bbox gold |
| FinRAGBench-V public page-image slice | 可提高公开 benchmark 说服力，但依赖 2.378GB archive 传输 | 固定 revision d0d65255c94e687caa81ac9da7758ed25ff046a5 | 外部下载；无人工标注 | 是，但只有资源可得时 | BLOCKED；不能用 metadata 代替 page-image score |
| Cross-page table continuity | 真实金融 PDF 常跨页；单页 TableIR 不足 | HSBC Annual Report / Pillar 3 | 20–30 multi-page tables；人工 continuity labels | 是 | MISSING |
| Version/freshness retrieval | 旧文档击败新文档是金融事故路径 | 可追加固定版本 corpus | 30–50 versioned questions | 是 | 当前已有 provenance，但没有正式 retrieval eval |

## P2 gaps

| 缺口 | 为什么重要 | 可复用数据 | 最小实验规模/人工量 | 当前是否值得为了简历补 | 现状 |
|---|---|---|---:|---|---|
| Answer generation accuracy | 评估最终回答，但会把 scope 扩到 generator 与 judge | TAT-QA/FinQA、RealFinance-v1 | 100 cases + answer/claim gold | 暂不值得 | MISSING；当前项目主线是 retrieval/evidence |
| Unsupported claim rate / abstention F1 | 对上线安全重要，但依赖 answerable split 和 claim annotation | 新建 answerability subset | 50–100 cases | 后续值得 | MISSING |
| Model/provider cost per query | 当前都是本地 CPU reference，没有 token billing | 现有 query traces | 固定硬件/模型；成本模型另建 | 暂不值得 | 无可靠 monetary estimate |
| Million-page throughput / sharding | 当前 backend 是 in-memory CPU | 需要规模化 corpus 或 synthetic capacity test | 独立系统 benchmark | 暂不值得 | NOT_IMPLEMENTED |
| ACL/ABAC leakage | 银行部署必须测，但会引入用户/权限数据模型 | 需要授权测试 corpus | 30–50 auth cases | 进入 production 前值得 | 当前仅有 security boundary，不是完整 ACL/ABAC |
| Drift / re-index / deletion | 线上维护与 freshness 必需 | 需要版本、更新、删除 fixtures | 30–50 lifecycle cases | 后续值得 | MISSING |

## 已有指标不能替代的东西

| 已有指标 | 不能替代 |
|---|---|
| Recall@5 / Recall@10 | claim support、answer correctness、abstention |
| Complete Evidence Rate | requirement decomposition accuracy（除非 requirement 是 gold） |
| Raw self coverage | independent evidence completeness |
| Independent CER | semantic entailment accuracy 或最终答案准确率 |
| HN Error | 泛化 ranking quality、neural reranker quality |
| Structure invariant | semantic table accuracy |
| Page Recall | bbox/region grounding、claim-level citation |
| FAER / answer eligibility | abstention precision/recall/F1 |
| API smoke test | throughput、SLA、HA、security、production readiness |

## 推荐补测顺序

如果只补三项：

1. 30–50 cases 的 claim-level citation support 与 page/block evidence gold。
2. 20–30 个真实 HSBC table regions 的 semantic TableIR gold。
3. 50–100 cases 的 answerable/unanswerable/partial evidence split，并计算 abstention 与 unsupported claim rate。

如果目标是 RAG 算法面试，再加：

4. RealFinance chunk granularity 与 page/block/cell granularity ablation。
5. 30–50 cases 的 version/freshness retrieval test。

如果目标是 multimodal 面试，再加：

6. 30–50 个真实 chart/figure/table region 的 bbox/region gold。
7. FinRAGBench-V slice 只有在 archive 可稳定取得时才补；不要为其修改当前 frozen slice。

## 本阶段审计结论

## P0-J progress: final RAG evaluation contracts

P0-J implemented deterministic scoring contracts for claim-level citation,
financial table semantics and answerability/abstention. It generated a
candidate-only queue from frozen project evidence: 50 RealFinance citation
cases, 24 B4.1 HSBC TableIR regions and 60 answerability candidates. The last
track is answerable-only and cannot be promoted to a balanced
`FinancialAnswerability-v1` without real review and partial/unanswerable
examples.

The repository still has no human-verified rows. Therefore Citation P/R/F1,
Claim Support Rate, Unsupported Citation Rate, semantic table accuracy and
abstention metrics remain `N/A`, not zero. This closes the evaluator contract
gap but does not close the annotation gap. The blocked run is under
`artifacts/final_rag_eval/`; the full explanation is in
`docs/FIN_EVIDENCE_FINAL_RAG_EVALUATION.md`.

当前项目最完整的是：

- evidence provenance 与可追踪对象；
- real-finance retrieval 的公开 fixed slice；
- independent coverage / eligibility gate；
- project-created HSBC financial facet hard-negative ranking；
- scoped structure-preserving TableIR；
- Evidence Backend v1 contract。

当前最缺的是：

- canonical human-verified requirement/table/citation gold；
- claim-level final answer evaluation；
- public FinRAGBench-V page-image closure；
- chunk/granularity ablations；
- production security and scale evaluation。

这些缺口是测评缺口，不应该用新增 feature 掩盖。
