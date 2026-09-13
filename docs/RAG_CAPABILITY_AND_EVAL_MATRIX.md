# FinEvidence RAG Capability and Evaluation Matrix

> 生成日期：2026-09-14
> 审计对象：D:\01_work\Enterprise Multimodal RAG\finevidence
> 规则：只汇总已存在的代码、冻结 manifest、正式报告和实验 artifacts；不修改历史结果，不把 N/A 当作零，不把结构 invariant 当作语义 accuracy。

## 使用说明

这张表按完整 RAG 链路组织，而不是按 P0/B3/B4 历史阶段组织。

状态枚举：

- IMPLEMENTED：代码或契约已存在，并且有可追踪的运行证据。
- PARTIAL：能力有实现或局部实验证据，但语义、规模、gold 或生产边界尚未闭合。
- NOT_IMPLEMENTED：当前没有该能力的可信实现或正式运行。
- BLOCKED：目标明确，但外部资源或关键条件尚未满足。

结论强度枚举：

- HUMAN_VERIFIED：真实人类逐条确认；本次审计没有把模型辅助结果提升到此级别。
- PUBLIC_BENCHMARK：使用公开数据集/公开 benchmark 的固定 slice。
- PROJECT_CREATED_NATURAL：项目从真实公开文档中 performance-blind 构造的自然控制集。
- PROJECT_CREATED_STRESS：项目构造的压力测试集，不能代表自然分布。
- MODEL_ASSISTED：模型辅助标注或裁决，human_verified=false。
- STRUCTURAL_INVARIANT：结构不变量或 round-trip 检查，不代表语义正确。
- OBSERVED：来自实际运行或仓库状态的观察。
- N/A：没有可靠 gold、没有可运行模型、数据未取得或不适用。

## 总矩阵

| RAG阶段 | 能力 | 状态 | 数据集 | 样本数 | 指标 | 当前结果 | 证据来源 | 结论强度 | 缺口 |
|---|---|---|---|---:|---|---|---|---|---|
| 数据接入与文档解析 | HSBC 官方 PDF provenance | IMPLEMENTED | HSBC FY2025 corpus | 2 docs / 494 pages | SHA256、page_count | Annual Report 372 pages；Pillar 3 122 pages；两份 PDF 均有 URL、时间、大小、SHA256 | data/hsbc_corpus_manifest.json | OBSERVED | PDF 不是仓库提交对象；没有全 archive |
| 数据接入与文档解析 | 确定性页面渲染 | IMPLEMENTED | HSBC page images | 494 pages | render hash、width、height、DPI | 72 DPI；页面 render manifest；B3 使用真实 page images | artifacts/hsbc_page_images/page_render_manifest.json；reports/b3-1-public-benchmark-evaluation-closure.md | OBSERVED | 未测多 DPI/渲染器对下游效果的消融 |
| 数据接入与文档解析 | 文本抽取与 page/block Evidence IR | IMPLEMENTED | RealFinance-v1、HSBC corpus | 1652 evidence；HSBC parsed pool | evidence identity、page、provenance | 可定位到 document/page/block；Backend smoke catalog_size=984 | benchmarks/real_finance_v1/manifest.json；docs/FIN_EVIDENCE_API_SPEC.md；reports/b3-1-public-benchmark-evaluation-closure.md | OBSERVED | text extraction accuracy 没有独立人工 gold |
| 数据接入与文档解析 | geometry-assisted table structure | PARTIAL | HSBC FY2025 Annual Report pages 1–26 | 24 regions / 13 pages | parse success、structure recoverable、header path、identity、row/column relation | parse success=1.0000；structure recoverable=0.7418；header path=0.7278；identity=1.0000；row/column relation=1.0000 | reports/b4-1-real-financial-table-recovery.md；artifacts/b4_1_runs/20260914T013551 | STRUCTURAL_INVARIANT | cell value、header semantics、unit、merged cell、footnote accuracy=N/A |
| 数据接入与文档解析 | 表格语义正确性 | NOT_IMPLEMENTED | HSBC TableIR | N/A | cell value、row/column mapping、header、unit、merged、footnote | N/A；没有 verified canonical TableIR gold | reports/b4-1-real-financial-table-recovery.md | N/A | 需要真实人工标注的小型 table gold |
| 数据接入与文档解析 | 复杂版面/图表解析准确率 | NOT_IMPLEMENTED | HSBC / public multimodal | N/A | table detection P/R、chart extraction、reading order accuracy | MISSING | reports/b3-1-public-benchmark-evaluation-closure.md；reports/b3-2-benchmark-integrity-public-closure.md | N/A | 需要页面级与区域级 gold |
| 切分、结构化与索引 | page/block Evidence IR | IMPLEMENTED | MiniFinance、RealFinance、HSBC | 19；1652；HSBC corpus | identity、source hash、page | 已实现；EvidenceObject 保留 identity、provenance、content、financial、structure、verification | src/finevidence/contracts/evidence.py；docs/FIN_EVIDENCE_ARCHITECTURE.md | OBSERVED | 没有 page/block/cell granularity 的正式消融 |
| 切分、结构化与索引 | text retrieval index | IMPLEMENTED | MiniBench-v1、RealFinance-v1、HSBC | 30；100；HSBC pool | Recall、MRR、nDCG | 有 Dense、BM25/Hybrid、facet-aware 与 page-text 实验 | reports/p0-d-real-finance-validation.md；reports/b3-2-benchmark-integrity-public-closure.md | PUBLIC_BENCHMARK | embedding/overlap/chunk size 消融 MISSING |
| 切分、结构化与索引 | visual page index | IMPLEMENTED | HSBC rendered pages | 81 indexed visual pages in B3.1 | image embedding/index time | CPU OpenAI CLIP RN50 实际读取 page images；visual index 6535.76 ms | reports/b3-1-public-benchmark-evaluation-closure.md | OBSERVED | CLIP 不是金融专用视觉模型；public visual slice 未闭环 |
| 切分、结构化与索引 | structured table index | PARTIAL | HSBC TableIR | 24 regions | TableIR query/retrieval | T2 deterministic executor；table-category R@10=0.0833；critical recovery=0.1667 | reports/b4-1-real-financial-table-recovery.md | STRUCTURAL_INVARIANT | 语义 cell accuracy 与跨页/merged/footnote gold=N/A |
| 切分、结构化与索引 | chunk size / overlap ablation | NOT_IMPLEMENTED | RealFinance-v1 | N/A | retrieval delta | MISSING | audit of reports/artifacts | N/A | 需要固定 query、至少 3 个 granularity 条件 |
| 切分、结构化与索引 | page vs block vs cell granularity comparison | NOT_IMPLEMENTED | Financial corpus | N/A | Recall/coverage/latency | MISSING | audit of reports/artifacts | N/A | 需要同一 corpus 的可比索引与 gold |
| 查询理解与证据需求拆解 | Required Fact heuristic | PARTIAL | RealFinance-v1 | 100 | Fact Precision / Recall | 0.0100 / 0.0017 | reports/p0-d-real-finance-validation.md | PUBLIC_BENCHMARK | flat decomposition 对多事实、derived、explanatory roles 不足 |
| 查询理解与证据需求拆解 | D0 Heuristic | PARTIAL | RequirementAdjudicated-v1 | 36 | Req P/R、critical recall、count error | Req P/R=0/0；critical recall=0；type acc=1.0000；count error=1.3056 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | MODEL_ASSISTED | adjudicated set 不是 human gold |
| 查询理解与证据需求拆解 | D1 LLM Direct | NOT_IMPLEMENTED | RequirementAdjudicated-v1 | 36 | requirement metrics | N/A；36/36 malformed JSON，未进入质量评分 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | N/A | 需要通过 schema contract 的真实 local/provider LLM |
| 查询理解与证据需求拆解 | D2 Schema Constrained | PARTIAL | RequirementAdjudicated-v1 | 36 | Req P/R、critical、role | Req P/R/critical=0.2778；role=1.0000 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | MODEL_ASSISTED | evidence mapping agreement=0.2315，gold 质量有限 |
| 查询理解与证据需求拆解 | D3 Evidence Aware | PARTIAL | RequirementAdjudicated-v1 | 36 | Req P/R、critical、independent CER | Req P/R/critical=0.2778；independent/critical=0 on adjudicated evaluation | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | MODEL_ASSISTED | mapping 与语义 verifier 仍弱 |
| 查询理解与证据需求拆解 | D4 Requirement Graph | PARTIAL | RequirementAdjudicated-v1 | 36 | Req P/R、critical、type/role/dependency | Req P/R/critical=0.7222；type/role/dependency=1.0000；count error=0 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | MODEL_ASSISTED | graph template 与 adjudication 有 annotation ceiling；非 human gold |
| 召回 | MiniBench dense | IMPLEMENTED | MiniBench-v1 | 30 questions | Recall@5 | 0.7586 | reports/p0-d-real-finance-validation.md | PROJECT_CREATED_STRESS | development fixture，不是 public benchmark score |
| 召回 | MiniBench hybrid | IMPLEMENTED | MiniBench-v1 | 30 questions | Recall@5 | 0.7931 | reports/p0-d-real-finance-validation.md | PROJECT_CREATED_STRESS | 受控数据，不能外推 |
| 召回 | RealFinance dense | IMPLEMENTED | RealFinance-v1 | 100 | R@5 / MRR / nDCG@10 / CER | 0.0900 / 0.1027 / 0.0773 / 0.0300 | reports/p0-d-real-finance-validation.md | PUBLIC_BENCHMARK | 100-case fixed slice；非完整 TAT-QA/FinQA leaderboard |
| 召回 | RealFinance hybrid | IMPLEMENTED | RealFinance-v1 | 100 | R@5 / MRR / nDCG@10 / CER | 0.1417 / 0.1895 / 0.1405 / 0.0500 | reports/p0-d-real-finance-validation.md | PUBLIC_BENCHMARK | hybrid 有提升但完整 evidence 仍低 |
| 召回 | RealFinance facet-aware | PARTIAL | RealFinance-v1 | 100 | R@5 / MRR / nDCG@10 / CER | 0.1417 / 0.1912 / 0.1398 / 0.0500 | reports/p0-d-real-finance-validation.md | PUBLIC_BENCHMARK | predicted facet 与 gold facet 的全面差异仍缺 |
| 召回 | HSBCNaturalHard dense | IMPLEMENTED | HSBCNaturalHard-v1 | 59 | R@5 / MRR / nDCG@10 / HN Error / Top1 | 0.1864 / 0.1312 / 0.1290 / 0.3898 / 0.0847 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | PROJECT_CREATED_NATURAL | 项目创建、model-assisted adjudicated |
| 召回 | HSBCNaturalHard hybrid + generic | IMPLEMENTED | HSBCNaturalHard-v1 | 59 | R@5 / MRR / nDCG@10 / HN Error / Top1 | 0.2881 / 0.2322 / 0.3364 / 0.3898 / 0.0847 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | PROJECT_CREATED_NATURAL | 真实 HSBC 文档，不是 HSBC 官方 benchmark |
| 召回 | HSBCNaturalHard facet-aware | IMPLEMENTED | HSBCNaturalHard-v1 | 59 | R@5 / MRR / nDCG@10 / HN Error / Top1 | 0.9661 / 0.7759 / 0.8313 / 0.0339 / 0.6441 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | PROJECT_CREATED_NATURAL | deterministic facet scoring，不是 neural reranker |
| 召回 | HSBCNaturalMultimodal T0 | IMPLEMENTED | HSBCNaturalMultimodal-v1 | 80 | Recall@10 | 0.5375 | reports/b3-2-benchmark-integrity-public-closure.md | PROJECT_CREATED_NATURAL | per @1/@5/MRR 等不是本审计的新增测评 |
| 召回 | HSBCNaturalMultimodal T1 Parsed Page Text | IMPLEMENTED | HSBCNaturalMultimodal-v1 | 80 | Recall@10 | 0.5875 | reports/b3-2-benchmark-integrity-public-closure.md | PROJECT_CREATED_NATURAL | 不是真实 Structured Table IR |
| 召回 | HSBCNaturalMultimodal V0 | IMPLEMENTED | HSBCNaturalMultimodal-v1 | 80 | Recall@10 | 0.0750 | reports/b3-2-benchmark-integrity-public-closure.md | PROJECT_CREATED_NATURAL | visual 是窄 fallback；使用 CLIP RN50 |
| 召回 | HSBCNaturalMultimodal M1 | IMPLEMENTED | HSBCNaturalMultimodal-v1 | 80 | Recall@10 | 0.5625 | reports/b3-2-benchmark-integrity-public-closure.md | PROJECT_CREATED_NATURAL | conditional 结果略低于 T1 |
| 召回 | HSBCVisualStress | PARTIAL | HSBCVisualStress-v1 | 60 | T0/T1/V0/M0/M1 R@10 | 0 / 0.0333 / 0.1000 / 0.0500 / 0.0500 | reports/b3-2-benchmark-integrity-public-closure.md | PROJECT_CREATED_STRESS | 固定模板与 keyword page selection 带来 construction bias |
| 排序 | FinanceHardSet facet-aware | IMPLEMENTED | FinanceHardSet-v1 | 100 | R@5 / MRR / nDCG@10 / HN Error | 1.0000 / 1.0000 / 1.0000 / 0.0000 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | PROJECT_CREATED_STRESS | 受控 hard-negative fixture |
| 排序 | HSBCNaturalHard deterministic financial facet | IMPLEMENTED | HSBCNaturalHard-v1 | 59 | HN Error / Oracle Gap | 0.0339 / 0.0000 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | PROJECT_CREATED_NATURAL | 不是 neural reranker；selection effect 仍存在 |
| 排序 | Neural reranker | NOT_IMPLEMENTED | HSBC / RealFinance | N/A | neural reranker quality | N/A | audit of src/finevidence/ranking and reports | N/A | 当前是 deterministic facet scorer / RRF / weighted fusion |
| 失败恢复、补检、表格与多模态升级 | Gold-fact targeted retrieval | IMPLEMENTED | RealFinance-v1 | 100 | Initial CER / Final CER / Recovery / FAER | 0.0300 / 0.8900 / 0.8866 / 0.0000 | reports/p0-d-real-finance-validation.md | PUBLIC_BENCHMARK | 使用 gold required facts；不是 predicted decomposition 结果 |
| 失败恢复、补检、表格与多模态升级 | Controlled targeted retrieval | IMPLEMENTED | EvidenceCompleteness-v1 | 30 | Initial CER / Final CER / Recovery / FAER | 0 / 1 / 1 / 0 | reports/p0-d-real-finance-validation.md | PROJECT_CREATED_STRESS | controlled fixture |
| 失败恢复、补检、表格与多模态升级 | Table T2 executor | PARTIAL | HSBCVisualStress-v1 + table-category subset | 60 / 24 cases | R@1 / R@5 / R@10 / critical recovery | all-60 retrieval=0.0167 / 0.0833 / 0.0833；table recovery=5/24=20.8333%；critical recovery=4/24=16.6667% | reports/b4-1-real-financial-table-recovery.md | OBSERVED | semantic table recovery 未证明 |
| 失败恢复、补检、表格与多模态升级 | Failure-aware route E1 | PARTIAL | HSBCVisualStress-v1 | 60 | route accuracy / R@10 / critical coverage | route acc=0.5000；R@10=0.0833；critical recovery=0.0833；visual invocation=0.5000 | reports/b4-structure-preserving-evidence-ir-failure-aware-escalation.md | PROJECT_CREATED_STRESS | route heuristic 非 learned classifier；table capability 缺失 |
| 失败恢复、补检、表格与多模态升级 | Conditional multimodal routing | PARTIAL | HSBCMultimodalRouting-v1 | 30 | precision / recall / invocation / unnecessary / net | precision=0.4348；recall=1.0000；invocation=0.7667；unnecessary=0.6500；net@10=+2 | reports/b3-1-public-benchmark-evaluation-closure.md | PROJECT_CREATED_STRESS | 当前 workload 未证明 cost saving |
| 证据校验与回答资格 | Fact–Evidence Alignment | IMPLEMENTED | P0-G / RealFinance-v1 | 100 | support type、matched/mismatched slots、reuse events | 显式 alignment 与 reuse policy 已实现 | reports/p0-g-evidence-requirement-graph.md；src/finevidence/evidence/alignment.py | OBSERVED | semantic entailment verifier 仍 deterministic |
| 证据校验与回答资格 | Independent Coverage | IMPLEMENTED | P0-G | 100 | D3 raw/self/independent/critical | D3 raw self=1.0000；independent CER=0.7283；critical=0.7400；invalid reuse=0.4100；FAER=0.4100 | reports/p0-g-evidence-requirement-graph.md | PROJECT_CREATED_STRESS | predicted requirement set 与 gold set 要分开读 |
| 证据校验与回答资格 | Adjudicated requirement coverage | PARTIAL | RequirementAdjudicated-v1 | 36 | D4 independent CER / critical | 0.3704 / 0.3750；adjudicated evidence ceiling=0.2593 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md | MODEL_ASSISTED | evidence mapping agreement=0.2315；非 human gold |
| 证据校验与回答资格 | Answer eligibility / sufficiency gate | IMPLEMENTED | RealFinance-v1 / P0-G | 100 | FAER / eligible rate | Top-K RAG FAER=0.1200；Coverage Gate/Targeted FAER=0.0000；D4 eligible rate=0.3800 | reports/p0-d-real-finance-validation.md；reports/p0-g-evidence-requirement-graph.md | OBSERVED | 这是资格/阻断指标，不是最终 answer accuracy |
| 生成、引用与最终回答 | Backend v1 search/coverage/verify/citation API | IMPLEMENTED | Local Evidence Backend v1 | smoke catalog 984 | HTTP contract / smoke | health OK；search、coverage、table/query、verify、citation routes 已实现 | docs/FIN_EVIDENCE_API_SPEC.md；docs/FIN_EVIDENCE_V1_RELEASE.md | OBSERVED | 不等于 production performance 或最终回答质量 |
| 生成、引用与最终回答 | Answer generation quality | NOT_IMPLEMENTED | Financial QA | N/A | Answer Accuracy、F1、numerical accuracy | MISSING | audit of reports/artifacts | N/A | 需要固定 generator、answer gold、claim-level scoring |
| 生成、引用与最终回答 | Claim support / citation quality | NOT_IMPLEMENTED | Financial QA | N/A | Citation P/R/F1、Claim Support Rate | MISSING；page hit 不能替代 claim support | audit of reports/artifacts；docs/FIN_EVIDENCE_API_SPEC.md | N/A | 需要 claim→evidence→page/block/region gold |
| 生成、引用与最终回答 | Abstention quality | NOT_IMPLEMENTED | Answerable/unanswerable QA | N/A | Abstention P/R/F1、unsupported claim rate | MISSING | audit of reports/artifacts | N/A | 需要 unanswerable 与 partial evidence 标注 |
| 生成、引用与最终回答 | Production-scale serving | NOT_IMPLEMENTED | Production corpus | N/A | throughput、SLA、availability、cost | MISSING；当前为 in-memory CPU backend | docs/FIN_EVIDENCE_V1_RELEASE.md；docs/FIN_EVIDENCE_ARCHITECTURE.md | N/A | 属于后续 hardening，不应写成当前成果 |

## 按阶段的账本结论

### P0-J 最终 RAG 评测闭环（当前状态）

P0-J 已新增可执行的 claim citation、table semantic 和 answerability
评测契约，并从冻结数据导出 50/24/60 条候选审核队列。由于仓库没有任何
`human_verified=true` 标注，三条正式质量结果仍为 `N/A`；候选投影不能被
称为 human gold，也不能被用来填充零分。详见
`docs/FIN_EVIDENCE_FINAL_RAG_EVALUATION.md` 和
`artifacts/final_rag_eval/`。

| Track | 当前状态 | 可报告结论 |
|---|---|---|
| Claim-level citation support | PARTIAL | contract + 50 candidate rows；Citation P/R/F1、Claim Support Rate、Page/Block/Cell Accuracy = N/A |
| Verified financial table semantic gold | PARTIAL | 24 B4.1 regions queued；cell/header/unit/period/entity/merged/footnote = N/A |
| Financial answerability / abstention | PARTIAL | 60 answerable-only candidates；partial/unanswerable verified split 缺失，全部最终指标 = N/A |

### 1. 数据接入与文档解析

最强证据是 provenance 完整和局部结构 invariant：

- HSBC 两份官方 PDF：494 pages，均有 source URL、download time、SHA256、file size、page count。
- B4.1 的 TableIR 在 24 个 region 上实现了 parse success、cell identity 和 row/column relation 的结构性检查。
- 这些结果不包含 semantic cell accuracy、merged-cell accuracy、unit accuracy 或 footnote accuracy。

### 2. 切分、结构化与索引

page/block Evidence IR、text index、visual page index 和局部 TableIR index 已存在。还没有 chunk granularity、overlap、page/block/cell 对照实验，因此不能说当前索引粒度已经最优。

### 3. 查询理解与证据需求拆解

D4 在 36-case model-assisted adjudicated set 上的 requirement P/R/critical recall 为 0.7222，比 D0/D2 的 0 或 0.2778 高，但这不是 human gold 结论，且 annotation template 与 D4 有 ceiling effect。D1 必须写成 N/A，不是 0 accuracy。

### 4. 召回与排序

RealFinance 的 Hybrid R@5=0.1417，高于 Dense 的 0.0900，但完整 evidence rate 只有 0.0500。HSBCNaturalHard 上 facet-aware deterministic scoring 将 HN Error 从 0.3898 降到 0.0339，但这不是 neural reranker 结果，也存在 selection effect。

### 5. 恢复、表格与多模态

Gold-fact targeted retrieval 的 RealFinance Final CER=0.8900 证明“知道缺什么后补检有价值”，不证明系统能自动正确识别缺失 fact。T2 TableIR 在限定 table slice 上恢复 5/24 page cases，但 semantic correctness 仍 N/A。自然 HSBC 多模态控制集上 T1=0.5875、T0=0.5375、V0=0.0750，视觉没有普遍优势。

### 6. 证据校验与回答资格

P0-G 是最强的安全性结论：D3 raw self coverage=1.0000，但 independent CER=0.7283，critical coverage=0.7400，invalid reuse=0.4100。下降代表 gate 找到了假完整性，不代表模型性能回退。

### 7. 生成、引用与最终回答

Backend v1 的 API contract 已实现并通过 smoke test，但回答生成、claim-level citation、abstention 和 production SLA 均没有正式评测，统一写为 MISSING/N/A。

## 读取顺序建议

1. 先看本矩阵，定位阶段状态。
2. 再看 docs/RESUME_SAFE_METRICS.md，只取安全口径。
3. 需要补测时看 docs/RAG_EVAL_GAPS.md。
4. 需要追溯数字时查 artifacts/rag_audit/ 对应 row 的 source_file 与 artifact_path。
