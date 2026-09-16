# 对话知识库

> 项目：Production Multimodal RAG

### 2026-09-13｜P0-H Gold Requirement Validation & HSBC Natural Hard Cases

P0-H 建立了两个真实数据闭环。`RequirementAdjudicated-v1` 从冻结 `RealFinance-v1` 选取 36 cases（factual 10、comparison 4、numerical 18、trend 3、explanation 1），保存 dual-pass、adjudication、agreement 与 provenance；方法为 `dual_pass_model_assisted_adjudication`，`human_verified=false`，不是 human/expert gold，也不是 TAT-QA/FinQA 官方 canonical requirement set。`HSBCNaturalHard-v1` 从官方 HSBC FY2025 Annual Report（372 pages，SHA `94aab2f5c83d1060ee95d344f1915833869fe4502dc635e4ab9ca84f496ee94b`）与 FY2025 Pillar 3（122 pages，SHA `eb64c8f0fcd32648512979886bceddba7128558761c07948b50f6ecfa83a32f7`）的 492 page evidence items 中形成 59 个真实 block hard cases；它是 project-created stress benchmark，不是 HSBC official benchmark，PDF 未提交 Git。

最终 clean-commit reproducibility runs 为 `finevidence/artifacts/p0_h_runs/20260913T004424445930Z/` 和 `finevidence/artifacts/p0_h_runs/20260913T005105288692Z/`，均记录 commit `95885590e2b5d49fb61a8c448e4df4ae46142004`，正式产物逐文件 SHA-256 完全一致。D1 真实本地 SmolLM2-135M CPU 调用 36/36 为 `N/A / MALFORMED_LLM_JSON`；D4 Req Precision/Recall=`0.7222/0.7222`、Critical Recall=`0.7222`、Dependency Accuracy=`1.0000`，Independent CER=`0.3704`、Critical Coverage=`0.3750`、Raw Self Coverage=`0.5185`、Invalid Reuse Rate=`0.5000`，adjudicated evidence CER=`0.2593`。D4 的 annotation template overlap 是已知限制。

HSBC ranking：Dense/Hybrid+Generic HN Error=`0.3898`；predicted/adjudicated facets 与 financial-aware deterministic reranker 均 HN Error=`0.0339`、Recall@5=`0.9661`、MRR=`0.7759`、nDCG@10=`0.8313`、Top-1=`0.6441`；facet entity/metric/period/basis/geography accuracy=`1.0000`，其余缺少 gold slots 为 `N/A`；Ranking Oracle Gap=`0.0000`。B3 gate=`READY`，依据是 adjudicated requirements、Independent Coverage validation、HSBC fixed provenance、59 个有效 natural hard cases 和 failure localization 均满足；本轮未实现 Visual Retrieval，D1 N/A、非人工 annotation、page-only parser、bbox/视觉 evidence、ACL、版本冲突与 unanswerable 仍未证明。正式报告：`finevidence/reports/p0-h-gold-requirement-hsbc-natural-hardcases.md`。
>
> 文件用途：把与本项目有关的对话沉淀为可检索的知识、决策、假设、证据和待办。
>
> 记录原则：默认记录结论与可执行信息，不机械复制整段聊天；原始聊天仍以 Codex 对话为准。

## 使用约定

- 后续与本项目有关的对话，默认追加到本文件。
- 每条记录尽量包含：日期、主题、核心结论、关键依据、已作决策、待验证事项和下一步。
- 明确区分：已观察事实、推测/假设、已验证结论和未完成事项。
- 没有实际实验或证据支持的结果，不写成已验证成果。
- 如果项目内已有更具体的专题文档，本文档只保留索引和关键结论，避免重复维护。
- 涉及代码、实验或项目状态的结论，应优先用项目文件、命令输出和实验产物复核。

## 知识主题索引

| 主题 | 关键结论 | 相关文档 |
| --- | --- | --- |
| RAG 总体认识 | RAG 是可观测、可评测、可迭代的证据获取与生成链路，不是“向量数据库 + Embedding + LLM” | [项目总任务](<Production Multimodal RAG — Pain-Driven Developer Prompt.md>) |
| Ingestion | 数据解析、清洗、结构恢复和语义切分决定检索上限；解析成功不等于证据忠实 | [项目总任务](<Production Multimodal RAG — Pain-Driven Developer Prompt.md>) |
| Retrieval | 生产级检索应包含查询理解、元数据过滤、Dense/BM25 混合召回、融合和重排 | [项目总任务](<Production Multimodal RAG — Pain-Driven Developer Prompt.md>) |
| Evidence | 正确答案要求正确、完整、版本有效且权限允许的证据进入上下文 | [项目总任务](<Production Multimodal RAG — Pain-Driven Developer Prompt.md>) |
| Evaluation | 不能只看答案准确率，还要评估解析完整性、证据覆盖、引用、版本、权限、拒答、延迟和成本 | [项目总任务](<Production Multimodal RAG — Pain-Driven Developer Prompt.md>) |
| Observability | 必须保留从用户问题到答案与引用的完整链路，才能定位 bad case 和 regression | [项目总任务](<Production Multimodal RAG — Pain-Driven Developer Prompt.md>) |

---

## 会话记录

### 2026-09-13｜RAG 的核心价值在完整工程链路

#### 用户提出的核心观点

RAG 的实际效果大多数时候不是由 LLM 单独决定，而是由以下完整链路共同决定：

```text
原始数据
  ↓
Ingestion
  ↓
Indexing
  ↓
Retrieval
  ↓
Context Construction
  ↓
Generation
  ↓
Evaluation
```

固定 token 切分可能破坏表格和实体关系；索引不仅需要 Embedding，还需要产品、区域、版本、生效时间等 metadata；检索也不等于向量搜索，而是查询理解、过滤、混合召回、融合和重排组成的 ranking pipeline。

#### 已沉淀的结论

1. **生产级 RAG 不是向量搜索功能，而是 retrieval/evidence pipeline。**
2. **Ingestion 决定检索上限。** 如果解析、清洗、结构恢复或切分已经破坏事实，后续模型很难恢复。
3. **Retrieval 决定当前答案质量。** 如果正确 evidence 没有被召回，LLM 只能猜测、幻觉或拒答。
4. **Evaluation 决定系统能否持续变好。** 必须能判断错误来自 parser、chunking、retrieval、fusion、reranking、context、generation、citation、version 或 permission。
5. 需要额外重视三个生产能力：**Observability、Badcase Analysis、Feedback Loop**。
6. 最重要的评估对象不是“是否召回了一段相关文本”，而是：

   > 完成这个问题所需的 Evidence Set 是否完整、正确、最新、可引用且对当前用户可见。

#### 可用于面试的表述

> 我不会把 RAG 理解成一个向量搜索功能，而会把它设计成一个有明确数据契约、检索链路、上下文构造、答案约束、引用验证和线上可观测性的 retrieval pipeline。因为答案质量受正确证据是否被召回所约束：没有 evidence，就没有可靠的 grounded answer。

#### 生产级扩展链路

```text
Data Acquisition
  ↓
Parsing / Cleaning
  ↓
Semantic Chunking
  ↓
Enrichment / Metadata
  ↓
Indexing
  ↓
Query Understanding
  ↓
Hybrid Retrieval / Fusion
  ↓
Reranking
  ↓
Context Construction
  ↓
Generation
  ↓
Verification / Citation
  ↓
Evaluation
  ↓
Observability / Feedback / Continuous Improvement
```

#### 待验证事项

- 需要通过真实工业和金融文档实验，验证 Visual Retrieval、跨页证据、多模态证据、版本冲突、权限过滤和拒答机制分别在哪些 query 上产生实际收益。
- 需要建立 hard-case suite 和 failure taxonomy，而不是只用总体 Answer Accuracy 判断系统质量。
- 需要确认现有开源系统已经解决到什么程度，再决定本项目真正值得实现的差异化能力。

#### 下一步

- 先完成真实 production RAG failure 的调研和归类。
- 建立 `REAL_WORLD_RAG_FAILURES.md`、`EXISTING_SYSTEM_GAP_ANALYSIS.md`、`PROJECT_STRATEGY.md` 和 `BENCHMARK_AND_HARD_CASE_PLAN.md`。
- 在方案冻结前，不因技术名词本身引入 Parser、Vector DB、Reranker 或 VLM；每个组件都必须对应明确 Pain、Failure、Root Cause 和可测量实验。

---

### 2026-09-13｜建立项目对话知识库

#### 工作约定

用户要求：将与项目有关的每次聊天视为知识库来源，并在当前项目文件夹生成文档记录。

#### 已执行

- 已确认项目目录：`D:\01_work\Enterprise Multimodal RAG`
- 已创建本文档：`CHAT_KNOWLEDGE_BASE.md`
- 已记录本次对话的 RAG 核心认识、面试表述、生产级扩展链路和后续待验证事项。

#### 记录边界

本文档记录的是项目知识和决策沉淀，不替代源代码、实验报告、正式规格或原始聊天记录。对于代码实现和实验结果，应继续链接到对应的项目文件与可复现实验产物。

#### 状态

已建立，后续默认追加。

---

### 2026-09-13｜FinEvidence 银行级金融证据 RAG 纲要

#### 来源与状态

用户补充了一版拟冻结的项目开发纲要，原始粘贴文件位于：

`C:\Users\Admin（无密码）\.codex\attachments\e589da0d-99c0-462f-ae5d-686aeff07b42\pasted-text.txt`

当前状态：**候选冻结纲要，待来源复核与最小 baseline 证据确认**。文档内容提出了明确方向，但其中的岗位要求、benchmark 规模、开源项目能力和技术选型仍需逐项用第一方来源、仓库代码或实际运行结果验证。

#### 核心定位

项目名称：**FinEvidence — Bank-grade Multimodal Financial Evidence & RAG Platform**

核心目标：从真实金融披露中获取并验证金融证据，输出带有细粒度引用、权限控制、数据血缘、拒答机制和完整审计轨迹的答案。

核心链路：

```text
Question
  → Evidence Acquisition
  → Evidence Verification
  → Reasoning
  → Verified Answer
```

#### 纲要提出的重点问题

- 金融实体与指标高度相似，容易出现 metric disambiguation 错误。
- 同一问题可能需要 Annual Report、Data Pack、Pillar 3 等多份披露共同支持。
- 多级表头、脚注、合并单元格和跨页表格不能简单 flatten 成文本。
- 财务计算应保留输入单元格、公式和结果，不能只依赖 LLM 心算。
- 图表和页面布局包含 OCR 文本无法完整表达的证据。
- 需要 evidence sufficiency、claim-level verification 和 fine-grained citation。
- ACL 必须在检索前生效，不能生成后才过滤。
- 增量重索引必须经过 regression gate，并支持 promotion / rollback。

#### 当前优先级建议

```text
P0  HSBC/金融文档 ingestion → text + visual indexing → multi-stage retrieval
    → Evidence IR → page citation → FinRAGBench-V 或等价公开 benchmark baseline

P1  Financial Entity Resolution → hard-negative ranking → Table IR
    → executable calculation → evidence sufficiency → claim verification

P2  Graph retrieval → controlled agentic search → RBAC/ABAC
    → lineage/audit → incremental re-index/rollback → regression/observability
```

#### 重要约束

- 不因 ColPali、Qwen、Milvus、Neo4j、LangGraph 等名词本身实现功能。
- 每个模块必须经过 `PAIN → FAILURE → ROOT CAUSE → DESIGN → EXPERIMENT → EVIDENCE` 链路证明。
- 所有指标在实际运行前保持 `N/A` 或“待实测”，不得预填简历或 README。
- 公开 benchmark 是主证据，自建 HSBC stress set 只能作为补充评估。
- 当前项目范围暂以金融场景为主；工业、多医疗、法律等领域不作为当前实现范围。

#### 待复核清单

- HSBC 岗位描述中实际要求的内容和当前有效性。
- ICBCBench、FinRAGBench-V、CFQA 的真实数据、许可证、评估代码和适用边界。
- ViDoRe V3 与金融 benchmark 的关系，避免将不同 benchmark 的任务和指标混用。
- MinerU、RAGFlow、RAG-Anything、Microsoft ColPali 方案的实际代码能力、许可证和运行前置条件。
- Qwen/Qwen3-VL 相关模型的实际可用 checkpoint、硬件成本和 license。
- P0 是否能在当前机器和独立项目环境中完成；若不能，记录具体阻塞，不用架构图替代实验。

---

### 2026-09-13｜Phase 1 研究启动与候选系统审计

#### 已完成

- 当前工作区确认不是 Git 仓库，未在总工作区初始化 CodeGraph。
- 已在 `research/repos/` 完整拉取 6 个指定候选仓库：RAGFlow、RAG-Anything、Microsoft ColPali accelerator、AIEduRAG、Financial_Asset_QA_System、SalesBoost。
- 另行拉取 ICBCBench 和 FinRAGBench-V 作为 benchmark 代码仓库。
- 已为 8 个代码仓库建立并验证 CodeGraph 索引。
- 已完成候选仓库源码/README/测试入口的第一轮审计。

#### 可复现验证

- AIEduRAG：`python -m pytest test -q` → **146 passed, 7 warnings**。
- Financial_Asset_QA_System：完整测试收集阶段因当前解释器缺少 `fredapi`、`sse_starlette`、`jieba` 等依赖而失败；局部 citation/chunk/BM25 测试 → **10 passed, 2 failed**，失败与 `jieba` 缺失后的 tokenizer fallback 一致。
- RAG-Anything、Microsoft ColPali accelerator、FinRAGBench-V 源码通过 `python -m compileall -q .`。
- ICBCBench public data：objective 80 条、subjective 40 条，中英字段存在；metrics 脚本因没有 judged result 目录而不能直接运行。
- FinRAGBench-V 完整视觉 corpus 不在 Git clone 中，尚未下载，也未产生 benchmark 分数。

#### 第一版研究判断

当前最值得进入 P0 的不是堆叠 Agent 或基础设施，而是：

1. 金融表格/视觉证据的结构保真与 cell/page citation。
2. 跨页面/跨文档 required evidence set 的完整性判断与拒答。
3. 金融指标、年份、实体、版本的 hard-negative ranking。

权限过滤、claim verification、可执行计算、增量重索引/rollback 和 observability 作为后续治理/生产化门槛；是否实现以 P0 baseline 的真实 failure 为准。

#### 已生成项目文档

- `REAL_WORLD_RAG_FAILURES.md`：真实 failure register、来源和验证协议。
- `EXISTING_SYSTEM_GAP_ANALYSIS.md`：候选系统能力、边界、commit 和最小验证结果。
- `PROJECT_STRATEGY.md`：FinEvidence 的 P0/P1/P2 研究策略和 baseline ladder。
- `BENCHMARK_AND_HARD_CASE_PLAN.md`：benchmark 角色、数据门禁、指标和 H1–H12 hard cases。

#### 当前阻塞

- FinRAGBench-V 完整数据下载前需要确认磁盘、数据规模、许可证和可用切片。
- ICBCBench 需要先构造 prediction/judged-result 或直接调用纯评估函数，才能跑出分数。
- 当前未创建 FinEvidence 实现仓库或统一 `.venv`；下一步先做 benchmark/data manifest 和最小 dense baseline，不先搭完整技术栈。

#### 2026-09-13｜Benchmark 数据门禁与新增 issue 证据

- 对 Hugging Face `zhaosuifeng/FinRAGBench-V` dataset tree 做了只读 manifest 统计：43 个文件、约 188.31 GB；其中 corpus 约 181.70 GB、`pdfs_for_QA` 约 6.56 GB、citation labels 约 49 MB。完整数据未下载；Git clone 没有可运行的 corpus/query/qrels 闭环，不能声称已跑 benchmark。
- 新增生产 failure 证据：RAGFlow #15962（显式 parser_config 触发表格 chunking 失败）、#14768/#15456（跨租户访问控制问题）、RAG-Anything Discussion #174（表格行列混淆和幻觉值）。这些证据加强了 F2/F7，而不改变 P0 三个核心 failure 的优先级。
- 当前研究文档已把“候选仓库自述”“公开 issue/文档观察”“本地命令实测”“尚未验证假设”分开；任何性能提升数字仍保持 N/A。
- 在 `Financial_Asset_QA_System` 的独立 `.venv` 中运行了候选仓库自带 `backend/run_rag_audit.py` 最小本地检索基线：三条探针均返回 3 个结果；“收入和净利润的区别是什么”和“什么是可转债的强赎条款”的 top-1 都是教材书目信息页，“什么是市盈率”出现同一来源重复。该结果证明了文件级词面检索的 precision、去重和细粒度证据定位风险，但不是公开 benchmark 分数。

#### 2026-09-13｜P0 实现启动与首个可复现闭环

- 按冻结指令停止扩展调研，不再新增核心 failure、仓库或 benchmark；P0 固定为 Structure Fidelity、Evidence Completeness、Hard-negative Ranking。
- 在 `D:\01_work\Enterprise Multimodal RAG\finevidence` 新建独立 Python 项目，初始化 OpenSpec 和 Git；最新代码/规格提交为 `80b60f388dc60a6b083c2aecc4a25a4e922d4a63`，候选仓库保持不修改。
- 已实现最小 Evidence IR：document/page/block/bbox/modality/table-row-column/entity/metric/period/score/content_hash；manifest 变更与 hash 不匹配会在检索前阻断。
- 已建立 30 题、19 条 evidence 的 `mini-v1` 开发切片，执行 B0 Dense、B1 Hybrid+Generic Reranker、B2 Coverage、B3 Conditional Visual。
- 最新稳定结果：B0 Recall@5 `0.7586`、nDCG@10 `0.6053`、Complete Evidence `0.7586`、HN Error `0.7000`；B1 Recall@5 `0.7931`、nDCG@10 `0.6202`、Complete Evidence `0.7931`、HN Error `0.7000`；B2 沿用 B1 检索并输出 coverage/answer eligibility；B3 `N/A`，因为尚未配置视觉 encoder。
- 结果解释边界：这些是固定开发切片的 CPU baseline，不是 FinRAGBench-V/ICBCBench 分数，不代表已获得提升；B2 尚未加入 generation/targeted re-retrieval，B3 尚未进行真实 visual retrieval。

### 2026-09-13｜按实验结论推进 P0-B/P0-C

用户冻结了推进原则：停止按功能模块扩张，改为用可证伪的实验结论驱动开发。MiniBench-v1 必须保持 byte-for-byte 不变；当前阶段不进入 B3 visual，也不添加 Agent、GraphRAG、ACL、FastAPI、K8s。

本轮已在独立仓库 `D:\01_work\Enterprise Multimodal RAG\finevidence` 完成：

- `FactRequirement(fact_id, description, acceptable_evidence_ids)` 和向后兼容的字符串 fact 归一化。
- `fact_coverage_for_case`，以及 Initial Complete Evidence Rate、Final Complete Evidence Rate、Partial-to-Complete Recovery Rate、False Answer Eligibility Rate。
- bounded targeted retrieval：从 missing fact 生成 query，最多两轮，合并唯一 evidence ID，保存 initial/round/final trace；不使用 Agent loop。
- `EvidenceCompleteness-v1`：30 条 multi-fact development cases。
- `FinanceHardSet-v1`：100 条 hard-negative development cases，按 temporal、metric、related metric、entity、segment、basis、currency、geography、period type、table context 各 10 条覆盖。
- deterministic financial facet extraction、facet-aware reranking 和 hard-negative-aware pairwise ranking adapter。
- P0-B/P0-C runner 与标准产物：config、dataset manifest、predictions、metrics、failure cases、ranking table、sufficiency table、per-query/per-round trace。

实际验证：全量 pytest `25 passed`；同一 `configs/p0_bc_cpu.json` 连跑两次，两个 run directory 不同，但 `ranking_table.json` 与 `sufficiency_table.json` 字节内容一致。稳定 run 目录为 `finevidence\artifacts\p0_bc_runs\20260912T193620598730Z-7739efd4` 和 `finevidence\artifacts\p0_bc_runs\20260912T193744723802Z-f7209d8d`。

| Ranking variant | Recall@5 | MRR | nDCG@10 | HN Error |
|---|---:|---:|---:|---:|
| Dense | 1.0000 | 0.8000 | 0.8524 | 0.3000 |
| Hybrid + Generic Reranker | 1.0000 | 0.8500 | 0.8893 | 0.3000 |
| + Financial Facets | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| + Financial-aware Reranker | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

| Sufficiency strategy | Initial CER | Final CER | Partial→Complete Recovery | False Answer Eligibility |
|---|---:|---:|---:|---:|
| Top-K RAG | 0.0000 | 0.0000 | 0.0000 | 0.9000 |
| Coverage Gate | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Targeted Retrieval, max 2 rounds | 0.0000 | 1.0000 | 1.0000 | 0.0000 |

结果边界：上述 FinanceHardSet-v1 和 EvidenceCompleteness-v1 是受控开发夹具，不是 FinRAGBench-V、ViDoRe 或真实企业数据的公开成绩；当前 ranker 是 deterministic lexical/metadata adapter，不应表述为 neural reranker。100% recovery 只说明该固定夹具上的可复现实验结果，下一步需要外部真实切片验证泛化。首次 runner 运行曾因误用 hardset 检索器导致 30 条 coverage 全为 0，已通过独立 fit completeness retriever 修正；该过程证明了 per-dataset wiring 和 trace 对实验可信度的重要性。

最终 provenance run：`finevidence\artifacts\p0_bc_runs\20260912T194238271033Z-32c91647`，其 `config.json` 记录最终 Git commit `388b7bf25aba5ec801819380042a8884be24c603`，Python 3.12.10 / Windows 11；该 run 的 trace 为 30 行、failure cases 为 0 行。

最终代码版本追加 per-category HN Error 后，最终复现 run 为 `finevidence\artifacts\p0_bc_runs\20260912T194510302588Z-215a6ab3` 与 `finevidence\artifacts\p0_bc_runs\20260912T194530353818Z-28ec8d23`，两次 ranking/sufficiency JSON 完全一致，config 均记录 commit `27cb86b80f8d42e30852e8b6014ed5d36efef036`；两次均为 30 行 trace、0 行 failure cases。

### 2026-09-13｜P0-D 外部有效性切换

用户要求停止继续优化 `0.0/1.0` controlled fixtures，进入 Real-Finance Validation。保留 MiniBench-v1、FinanceHardSet-v1、EvidenceCompleteness-v1 完全冻结；不下载 FinRAGBench-V 全量 corpus。

已从公开 TAT-QA 与 FinQA 仓库构建 `RealFinance-v1`：TAT-QA 50 条 `table-text` dev questions、FinQA 50 条 answerable dev records，共 100 cases、1,652 个 Evidence IR items。TAT-QA 的 table/paragraph 来源、FinQA 的 `gold_inds`、`program`、`exe_ans` 均保留，source repository commit 和原始文件 SHA-256 写入 manifest。

P0-D 首个外部有效性结果：Dense Recall@5 `0.0900`、Hybrid `0.1417`；gold-fact Initial CER `0.0300`、Targeted Final CER `0.8900`、Recovery `0.8866`；仍有 11/100 条 gold-fact evidence cases 未完整恢复。Required Fact Precision `0.0100`、Recall `0.0017`，说明当前 deterministic decomposer 几乎不能从真实问题恢复 gold facts。预测 facts 的 self-coverage 为 `0.92→0.99`，但不应被解释为 gold-fact 成功，因为上游 Required Fact Recall 极低。

Facet extraction accuracy 和 gold-facet ranking 暂为 `N/A`：TAT-QA/FinQA 没有 canonical entity/metric/period facet labels。HSBC-Stress-v1 暂为 `N/A / LOCAL_PROVENANCE_SOURCE_MISSING`，没有把手工 fixture 冒充 naturally-occurring HSBC hard negatives。

P0-D 代码、固定派生数据、报告和最终 run 位于 `D:\01_work\Enterprise Multimodal RAG\finevidence`；实验代码提交为 `d97557d624b7dbe99ef6bff28acc057401d966a4`，报告为 `reports\p0-d-real-finance-validation.md`，最终可复现 run 为 `artifacts\p0_d_runs\20260912T202547160764Z-62a4fd11` 和 `artifacts\p0_d_runs\20260912T202612338140Z-c2f60731`。两次 run 的 metrics 与 dataset manifest 内容一致，各有 100 条 trace、11 条保留 failure cases；Top-K FAER `0.1200`，Coverage Gate/Targeted Retrieval FAER 均为 `0.0000`。这轮结果是 public source-derived dev slice 观测，不是 leaderboard 分数。

### 2026-09-13｜P0-E Evidence Requirement Understanding

P0-D 暴露的两个瓶颈被正式拆成 `Question → Required Facts` 与 `Required Facts → Evidence Mapping`。新增 P0-E runner，比较 D0 Heuristic、D1 LLM Direct、D2 Schema-constrained、D3 Evidence-aware。D1 因没有授权 provider 保持 `N/A`；TAT-QA/FinQA 没有 canonical structured fact labels，因此 Critical Fact Recall 和 Slot Accuracy 保持 `N/A`。

P0-E 在同一 RealFinance-v1 上的 gold evidence condition 为 Initial CER `0.0500`、Final CER `0.8900`、Recovery `0.8842`、FAER `0.0000`。D0 Fact Recall `0.0017`、D2/D3 `0.0033`；D0/D2 predicted evidence completion 为 `0.0000`，D3 因把一个候选证据复用于多个模板事实而为 `1.0000`，Oracle Gap `-0.1100`，并明确标记为 `NEGATIVE_GAP_PREDICTED_FACTS_NOT_CALIBRATED_TO_GOLD_FACTS`，不能当作提升。

两次 P0-E final run 的 metrics 与 dataset manifest 完全一致，各含 400 条 variant trace、200 条保留 unresolved mapping failure traces；代码提交为 `ea7876b4caad8aca9dee22fbb106a60a55bb14e7`，run 为 `finevidence\artifacts\p0_e_runs\20260912T205940827353Z-bc0c3c06` 和 `finevidence\artifacts\p0_e_runs\20260912T210052094393Z-edbc1aa9`。

P0-F 只建立了官方 HSBC FY2025 Annual Report/Pillar 3 URL manifest 和 opt-in 本地 fetcher，仓库不提交 PDF；没有本地 corpus 时 HSBC naturally-occurring hard-negative 仍为 `N/A`。B3 继续冻结，下一步只应提高 fact decomposition/mapping 并获取许可清晰的 HSBC 本地 source slice。

### 2026-09-13｜P0-G Evidence Requirement Graph & Fact–Evidence Alignment

P0-G 的唯一主线是：RAG 不能因为检索到相关 evidence 就获得回答资格，只有所有 critical evidence requirements 被正确角色、正确语义、可独立验证的 evidence 或合法 derivation 满足时才可回答。实现位于 `finevidence/src/finevidence/contracts/requirements.py`、`evidence/alignment.py`、`evidence/requirement_graph.py`、`eval/p0_g.py`；OpenSpec change 为 `openspec/changes/p0-g-evidence-requirement-graph/`。

当前 schema 支持 `RETRIEVED_FACT`、`DERIVED_FACT`、`EXPLANATORY_FACT`、`CONTEXT_FACT`，以及 role、entity、metric、period、segment、basis、geography、currency、unit、operation、criticality、depends_on 和 acceptable evidence。Graph 是 Python/Pydantic DAG，不是 GraphRAG/Neo4j。`EvidenceReusePolicy` 按 role/period/metric/entity 约束复用；同一 evidence 对不等价 role 的重复覆盖会生成 invalid reuse event，并从 Independent Coverage 排除。Derived Fact 只有在 dependencies 独立覆盖后才算满足；缺 critical requirement 会阻断 `answer_eligible`，缺 supporting requirement 可保留 partial result。

正式 P0-G run：`finevidence/artifacts/p0_g_runs/20260912T215237402336Z-d20699d7/` 与 `finevidence/artifacts/p0_g_runs/20260912T215349801181Z-e6d7cba3/`，代码 commit `429058ecbab4335922390d00026d3c4cf77b4e58`。两次 metrics、dataset manifest、per-query trace、requirement graphs、alignment results 和 failure cases 的 SHA-256 一致；各含 500 trace/graph/alignment rows，failure rows 372。Gold Independent CER=`0.9083`；D3 Raw Self=`1.0000`→Independent CER=`0.7283`、Critical Coverage=`0.7400`，Invalid Reuse Rate=`0.4100`、FAER=`0.4100`；D4 Independent CER=`0.5033`，不构成提升。

Failure taxonomy category counts：`CRITICAL_FACT_MISSING=303`、`EVIDENCE_MAPPING_FAILURE=303`、`EVIDENCE_REUSE_INFLATION=77`、`PREDICTED_REQUIREMENTS_UNDER_SPECIFIED=186`。D1=`N/A / LLM_PROVIDER_NOT_CONFIGURED`；`RequirementGold-v1`=`N/A / MANUAL_ANNOTATION_NOT_AVAILABLE`、0 cases，所以 Critical Fact Recall 和 Slot Accuracy 不伪造。HSBC 仍为 official URL manifest + opt-in fetcher，未下载固定本地 PDF corpus；B3 继续 blocked。详细报告：`finevidence/reports/p0-g-evidence-requirement-graph.md`。
## B3 — Multimodal Evidence Retrieval & Visual Grounding

P0-H remains frozen and was not re-run. B3 added page rendering, image Evidence IR, a real CPU OpenAI CLIP RN50 adapter, normalized fusion, coverage-aware routing, page citation evaluation, and a 60-case `HSBCVisualStress-v1` mined from real HSBC FY2025 pages. Formal code commit: `7589c57`; reproducibility runs: `finevidence/artifacts/b3_runs/20260913T114012` and `finevidence/artifacts/b3_runs/20260913T114144`.

Observed B3 result: Text R@5 0.0000, Structured 0.0000, Visual 0.0500, Fusion RRF 0.0167, Conditional 0.0167; visual critical recovery 0.0500, multimodal regression 0.0000, net recovery +3, visual invocation 100%. This is a negative/limited finding, not a production claim. `FinRAGBench-V-Slice-v1` metadata/qrels are fixed at 100 queries, but page-image evaluation remains N/A because the required Hugging Face archive timed out. B3 status is `PARTIAL`.
### 2026-09-13｜B3.1 Public Benchmark & Evaluation Closure

P0-H was not rerun. B3.1 upgraded the official Hugging Face client to `huggingface_hub==0.34.4` plus `hf_xet==1.6.0`, pinned `FinRAGBench-V-Slice-v1` to revision `d0d65255c94e687caa81ac9da7758ed25ff046a5`, and attempted only `pdfs_for_QA/pdf_en.tar.gz`; Xet and HTTP fallback remained at zero bytes, with traceback in `finevidence/data/finragbench_v_source/download_blocker.json`. Public page-image metrics remain `N/A`.

HSBCVisualStress-v1 remains 60 cases. New `HSBCMultimodalRouting-v1` contains 30 balanced real-page cases (10 each `TEXT_SUFFICIENT`, `TABLE_PARSED_SUFFICIENT`, `VISUAL_NEEDED`). T1 is `Parsed Page Text`; verified Structured Table IR is `N/A`. Recovery is explicit at @1/@5/@10. Final code commit is `52554ea096fdd846cde7981f269a2c245b2a1732`; two final runs have byte-identical metrics/rankings/failure outputs and natural CPU timing variance. B3 remains `PARTIAL`; no production hardening starts. Report: `finevidence/reports/b3-1-public-benchmark-evaluation-closure.md`.

### 2026-09-14｜B3.2 Benchmark Integrity & Public Closure

B3.2 保留 B3.1 的代码、数据和结果，正式代码 commit 为 `622381ced70447c2539f81004da77f64809d3adf`。对 `HSBCVisualStress-v1` 的 performance-blind 20-case audit 证实：60 条 case 由 10 个固定模板生成，positive page 由关键词命中选择；T0 page Recall @1/@5/@10/@50 为 `0/0/0/7`（@50=`0.1167`）。因此 `T0 Recall@10=0/60` 可复现，但 stress workload 存在 text-failure construction bias，不能解释成自然金融问题的 text baseline。

新建 `HSBCNaturalMultimodal-v1`：80 real HSBC page cases，Annual Report/Pillar 3 各 40，按照 corpus page hash 在任何 T0/V0 结果读取前选择，并排除 VisualStress candidate pages。Natural @10 Recall：T0=`0.5375`、T1 Parsed Page Text=`0.5875`、V0=`0.0750`、M1=`0.5625`。这组控制结果反驳了“视觉普遍胜出”的未支持叙事；Verified Structured Table IR 仍为 `N/A`。

B3.2 通过 WSL Ubuntu 使用官方 revision-pinned HF resolve URL 做了第二种 `wget -c` 传输尝试；响应包含正确 `X-Repo-Commit`、HTTP 200、Range 支持和 2,378,037,659 bytes 长度，但在 bounded attempt 内只传输 10,037,760 bytes，partial archive 未使用，FinRAGBench-V page-image metrics 仍 `N/A`。完整 blocker 位于 `finevidence/data/finragbench_v_source/`。B3=`PARTIAL`，B4 尚不进入。正式报告：`finevidence/reports/b3-2-benchmark-integrity-public-closure.md`。

### 2026-09-14｜B4 Structure-Preserving Evidence IR & Failure-Aware Escalation

B4 直接建立在 B3.2 之上，没有重做历史实验。新增 `TableIR`/`TableCell`：真实 TAT-QA source-array 的 15 个 unique tables 具备 1.0000 raw-value round-trip、cell identity 和 row/column relation；header path 覆盖率为 0.5830，caption/footnote/bbox 没有独立 gold，因此保持 N/A。HSBC 当前解析结果没有 verified cell-level table IR，不能把 Parsed Page Text 伪装成结构化 IR。

正式 B4 run 使用 commit `251b7a895c03a34e182a97058450ae436d21aab6`：`finevidence/artifacts/b4_runs/20260914T004659/` 与 `20260914T004750/`。E0 oracle route 只用于测量 headroom；E1 performance-blind predicted route accuracy=`0.5000`，visual invocation=`0.5000`，Predicted Failure Router Recall@1/@5/@10=`0.0167/0.0333/0.0833`，critical recovery=`0.0833`，@10 regression=`0.0000`。所有 route 仍通过 Evidence qualification。两次 run 的 metrics、rankings 和 failure rows 一致；timing-bearing traces 只比较结构化内容，不声称 byte-identical timing。

本地 public-corpus investigation 保留在 `data/finragbench_v_source/corpus_layout_investigation.json`：冻结 FinRAGBench-V revision 的 `corpus/en` 暴露 14 个 multi-gigabyte compressed shards，qrels 100-query slice 需要 504 unique corpus IDs，因此无法在不取 containing shard 的前提下逐页获取；public score 仍 N/A，B3 仍 `PARTIAL`。B4 在实验 scope 内完成，核心 hypothesis 以限定形式存活：视觉应是诊断后的窄路径，表格失败应优先由 structure-preserving IR 解决；E1 轻量 router 尚未解决 failure classification，也不授权 production hardening。报告：`finevidence/reports/b4-structure-preserving-evidence-ir-failure-aware-escalation.md`。

### 2026-09-14｜B4.1 Real Financial Table Recovery & Executable Structured Retrieval

B4.1 没有重做 B3/B4。固定代码 commit=`16137e652215edc83f01d044f5826e9787a7c15e`，真实 PDF extractor 使用 `pdfplumber` 的 positioned words/table regions，在 HSBC FY2025 Annual Report pages 1–26 接受 24 regions / 13 pages，并写出真实 `TableIR` cell evidence。`T2 Real Structured Table IR` 是 deterministic TableIR cell executor，保留 table_id/row_id/column_id/bbox；它不是 Parsed Page Text，也不是 neural reranker。

E0：structure recoverable rate=`0.7418`，header path population=`0.7278`，cell identity/row-column invariants=`1.0000`。semantic cell accuracy、unit accuracy、merged-cell accuracy、footnote semantics 因没有 verified human gold 保持 N/A。E1：在冻结 60-case `HSBCVisualStress-v1` 上 T2 R@1/@5/@10=`0.0167/0.0833/0.0833`、Independent Critical Coverage=`0.0667`；相对 T1，四类 table failure @10 恢复 5/24 页面与 4/24 critical qualification，regression=0。V0 @10=`0.1000`，T2+Text @10=`0.0833`，所以没有宣称 T2 或融合胜过视觉。

两次正式 run：`finevidence/artifacts/b4_1_runs/20260914T013358/`、`20260914T013551/`；结构、rankings、failure rows 一致，timing 因 CPU 负载变化。B4.1 在 scoped real-HSBC table-recovery experiment 内完成；B3 仍 `PARTIAL`，原因仍是 FinRAGBench-V public page-image closure 的外部下载 blocker。下一步如需语义 table claim，应先建立小型真实 human-verified TableIR subset；full production hardening 当前没有由此实验获得授权。
### 2026-09-14｜Evidence Backend v1

本轮没有重做 P0–B4。`finevidence` 新增 `EvidenceObject` 外部契约与 `EvidenceService`：`/api/v1/evidence/search`、`/coverage`、`/table/query`、`/verify`、`/{id}/citation` 和 `/health`。服务复用现有 CPU HybridRetriever、FactEvidenceAlignment 与 IndependentCoverage；citation 保留 document hash、page、table/row/column 和可选 bbox。没有配置 authorizer 时，tenant/user_role 安全过滤返回 403，避免把未授权 evidence 当成已过滤结果。新增 FastAPI contract tests、Docker local package、架构图和 Agent integration docs；不包含 Agent loop、UI、Kubernetes、ACL 实现或新的实验结论。代码与发布文档在 `finevidence/docs/`，OpenSpec 为 `finevidence/openspec/changes/evidence-backend-v1/`。

### 2026-09-14｜B5 Neural Retrieval & Controlled Agentic Search 起始增量

用户提出将 FinEvidence 从传统 `TF-IDF/SVD + hybrid + deterministic facets + CLIP` 逐步升级为现代 neural retrieval、late interaction、现代 visual retrieval、typed agentic search 和轻量 Evidence Graph。执行边界冻结为：先做 B5 只读审计与 B5.1 viability，不覆盖 P0–B4/P0-J 历史结果；模型只提升 candidate quality，不能绕过 Evidence Qualification、Independent Coverage、Critical Coverage、Failure Attribution 和 provenance。

审计产物：`finevidence/CURRENT_STATE_AUDIT.md`、`B5_IMPLEMENTATION_PLAN.md`、`B5_EXPERIMENT_MATRIX.md`、`docs/architecture/finEvidence-b5.architecture.json`。新增 OpenSpec：`finevidence/openspec/changes/b5-neural-retrieval-controlled-search/`，已通过 strict validation。新增 `QwenEmbeddingRetriever`、`TypedSearchController`、`EvidenceGraph` 和 `scripts/run_b5.py`；B5.1 run 为 `finevidence/artifacts/b5_1_runs/20260913T225833168129Z-5ac8669d/`。

B5.1 在冻结 `RealFinance-v1` 上复跑 current dense/hybrid：R1 R@1/@5/@10=`0.0400/0.0900/0.1117`、MRR=`0.1070`、nDCG@10=`0.0863`、CER=`0.0400`；R2=`0.0950/0.1417/0.1900`、MRR=`0.1969`、nDCG@10=`0.1593`、CER=`0.1000`。缓存 Qwen3 Embedding revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` 只有 tokenizer/config；HF/Xet 的 model.safetensors bounded fetch 显示约 1.19G 但 118 秒后仍 0 bytes，随后中止。formal R3/R4 均 `N/A`，没有执行真实 Qwen inference，也没有把 current hybrid 冒充 Qwen。

当前 B5.1=`PARTIAL / MODEL_WEIGHTS_BLOCKED`。Neural reranker、ColBERT、ColQwen、GraphRAG end-to-end 和 typed controller quality gate 尚未有可报告实验；保留为后续 viability-gated stages。相关结果/边界见 `finevidence/B5_RESULTS.md`、`B5_FAILURE_ANALYSIS.md`、`B5_DECISIONS.md`。
