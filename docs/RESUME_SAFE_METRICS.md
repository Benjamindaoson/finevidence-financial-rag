# FinEvidence Resume-Safe Metrics

> 目的：给简历、面试材料和项目介绍提供唯一的安全取数边界。
> 原则：每个数字都必须能回到正式报告或 artifact；如果一项能力没有可靠 gold，就写 N/A；不要把项目创建的 stress set 写成官方 benchmark。

## P0-J final evaluation status

P0-J created pure scoring contracts and candidate-only review queues for
claim-level citation, table semantics and answerability. No new formal metric
is resume-safe yet: there are no `human_verified=true` rows. Use
`docs/FINAL_RESUME_METRICS.md` for the compact safe list. Do not describe the
50 citation rows, 24 table regions or 60 answerability rows as human gold.

## A. 可以直接写，但仍要保留数据集和口径

这些指标有正式运行证据，适合写入简历。推荐使用“在……上”而不是裸报一个看似通用的百分比。

| 指标 | 数值 | 推荐写法 | 证据 |
|---|---:|---|---|
| RealFinance Hybrid Recall@5 | 14.17% | 在固定 RealFinance-v1（100 cases，50 TAT-QA + 50 FinQA）上，将 Hybrid Recall@5 测为 14.17%，Dense baseline 为 9.00%。 | reports/p0-d-real-finance-validation.md |
| RealFinance Hybrid Complete Evidence Rate | 5.00% | 在同一 100-case slice 上，Hybrid Complete Evidence Rate 为 5.00%；这说明完整 evidence set 仍是瓶颈。 | reports/p0-d-real-finance-validation.md |
| Gold-fact targeted Final CER | 89.00% | 在 gold required facts 已知的条件下，bounded targeted retrieval 将 RealFinance CER 从 3.00% 提升到 89.00%。 | reports/p0-d-real-finance-validation.md |
| P0-G D3 Independent CER | 72.83% | 在 P0-G 的 fixed evaluation 上，用 Independent Coverage 把 D3 的 raw self coverage=100.00% 重新审计为 72.83%。 | reports/p0-g-evidence-requirement-graph.md |
| P0-G Critical Coverage | 74.00% | 在同一 P0-G 条件下，D3 Critical Coverage 为 74.00%。 | reports/p0-g-evidence-requirement-graph.md |
| P0-G Invalid Evidence Reuse Rate | 41.00% | 检测到 41.00% 的 invalid evidence reuse events，阻断同一 evidence 被不等价 fact 复用造成的假完整性。 | reports/p0-g-evidence-requirement-graph.md |
| Controlled FinanceHardSet facet-aware HN Error | 0.00% | 在 FinanceHardSet-v1 的 100 个受控 hard-negative cases 上，facet-aware deterministic scoring 将 HN Error 测为 0.00%。 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md |
| HSBCNaturalHard facet-aware HN Error | 3.39% | 在项目创建的 59-case HSBCNaturalHard-v1 上，financial facet-aware deterministic scoring 的 HN Error 为 3.39%，Hybrid baseline 为 38.98%。 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md |
| HSBCNaturalHard facet-aware Top-1 Positive Rate | 64.41% | 在 HSBCNaturalHard-v1 上，facet-aware deterministic scoring 的 Top-1 positive rate 为 64.41%。 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md |
| HSBCNaturalHard facet-aware Recall@5 | 96.61% | 在 HSBCNaturalHard-v1 上，facet-aware deterministic scoring 的 Recall@5 为 96.61%。 | reports/p0-h-gold-requirement-hsbc-natural-hardcases.md |
| B4.1 TableIR structure invariants | 100.00% | 在真实 HSBC FY2025 Annual Report pages 1–26 的 scoped table probe 中，cell identity 与 row/column relation invariants 均为 100.00%。 | reports/b4-1-real-financial-table-recovery.md |
| B4.1 TableIR structure recoverable rate | 74.18% | 在同一 scoped probe 中，structure recoverable rate 为 74.18%；这是结构性可恢复率，不是语义表格理解准确率。 | reports/b4-1-real-financial-table-recovery.md |
| B4.1 T2 table page recovery | 20.83% | 在 24-case table-category slice 上，T2 在 cutoff@10 恢复 5/24=20.83% page cases。 | reports/b4-1-real-financial-table-recovery.md |
| Backend v1 automated tests | 81 passed | Evidence Backend v1 当前仓库测试套件 81 tests passed；这是代码回归证据，不是金融回答准确率。 | pytest -q output; docs/FIN_EVIDENCE_V1_RELEASE.md |

说明：RealFinance、FinanceHardSet、EvidenceCompleteness 的数据集性质不同；简历中必须同步注明 fixed slice、controlled fixture 或 project-created set。

## B. 可以写，但必须加限定

### 1. Project-created natural / stress benchmark

安全写法：

- “构建并评估了 59-case HSBCNaturalHard-v1 project-created natural hard-negative set。”
- “在 80-case HSBCNaturalMultimodal-v1 project-created natural control set 上，T1 Parsed Page Text Recall@10=58.75%，V0 CLIP visual Recall@10=7.50%。”
- “在 60-case HSBCVisualStress-v1 project-created stress set 上，B3.2 发现 fixed templates 与 keyword positive-page selection 导致 construction bias。”

不能写：

- “在 HSBC 官方 benchmark 上达到……”
- “在银行真实生产数据上达到……”
- “HSBC 官方认证的检索准确率……”

### 2. Model-assisted annotation

安全写法：

- “采用 dual-pass model-assisted adjudication 构建 RequirementAdjudicated-v1（36 cases，human_verified=false）。”
- “RequirementAdjudicated-v1 上 D4 requirement recall=72.22%，但该集合不是 human gold，也不是 TAT-QA/FinQA 官方 gold。”

不能写：

- “human-annotated gold”
- “expert-verified requirement set”
- “human-level requirement understanding”

### 3. Deterministic ranking

安全写法：

- “实现 financial facet-aware deterministic scoring / reranking adapter。”
- “在 HSBCNaturalHard-v1 上将 HN Error 从 38.98% 降到 3.39%。”
- “Ranking Oracle Gap=0.00%，说明该 slice 没有暴露 predicted facet extraction bottleneck；不说明通用 facet extraction 已解决。”

不能写：

- “训练了 neural financial reranker”
- “实现了企业级 learned reranker”
- “financial LLM reranker”

### 4. Visual retrieval

安全写法：

- “用 CPU OpenAI CLIP RN50 对真实渲染的 HSBC PDF pages 做了 page-level visual retrieval。”
- “在自然 HSBC control set 上，visual Recall@10=7.50%，因此视觉被保留为诊断后的窄路径 fallback。”
- “B3 VisualStress 的 @10 text-failure recovery=5.00%，但该 stress set 有 construction bias。”

不能写：

- “用 VLM 理解了金融图表”
- “视觉检索显著提升了金融 RAG”
- “multimodal retrieval 普遍优于 text retrieval”

### 5. Backend boundary

安全写法：

- “将 EvidenceObject、search、coverage、table/query、verify、citation 封装为版本化 FastAPI Evidence Backend v1。”
- “通过 local HTTP smoke test 验证 health、search、coverage、table/query、verify、citation contract。”
- “当前后端是 in-memory CPU reference implementation，供上层 AI Investment Research Agent 对接。”

不能写：

- “production-grade evidence platform”
- “高可用企业 RAG service”
- “已完成 RBAC/ABAC、SLA、million-page serving”

## C. 禁止写入简历或对外材料

以下内容当前没有足够证据，不能写成已完成成果：

- FinRAGBench-V public page-image final score；当前 archive blocker，所有正式 page-image metrics 是 N/A。
- human-level table understanding。
- semantic cell accuracy、merged-cell accuracy、unit association accuracy、footnote semantics。
- neural reranker；当前没有真正 learned neural reranker。
- enterprise VLM capability；CLIP RN50 是低基线视觉 embedding，不等于 VLM。
- production-grade RBAC/ABAC；当前只有 security boundary/hook，未完成完整权限系统。
- Answer Accuracy、Answer F1、Numerical Answer Accuracy。
- Citation Precision、Citation Recall、Citation F1、Claim Support Rate。
- Unsupported Claim Rate、Abstention Precision/Recall/F1。
- “visual always-on 更可靠”或“multimodal 普遍优于 text”。
- “B3 已 COMPLETE”；当前 B3 仍 PARTIAL。
- “HSBC 官方 benchmark”；HSBCNaturalHard、HSBCVisualStress、HSBCNaturalMultimodal 都是项目创建的集合。
- “API smoke test 证明 production performance”。
- “page hit 证明 claim 被正确支持”。

## 推荐的简历主叙事

### 中文

构建 Evidence-Qualified Retrieval 系统，面向高风险金融文档显式建模 requirement graph、fact–evidence alignment 与 independent critical coverage；在固定 RealFinance-v1 上测得 Hybrid Recall@5=14.17%，并用 Independent Coverage 识别 D3 raw self coverage=100% 背后的 41% invalid evidence reuse；在真实 HSBC 披露文档上实现 provenance-bearing Evidence IR、financial facet-aware deterministic ranking 和局部结构保持 TableIR，进一步封装为可供 AI 投研 Agent 调用的 Evidence Backend v1。

### English

Built an evidence-qualified retrieval system for high-stakes financial documents, modeling requirement graphs, fact–evidence alignment, and independent critical coverage; evaluated on a fixed RealFinance-v1 slice with Hybrid Recall@5=14.17% and exposed 41% invalid evidence reuse behind a 100% raw self-coverage result; implemented provenance-bearing Evidence IR, deterministic financial facet ranking, scoped TableIR recovery on public HSBC disclosures, and a versioned Evidence Backend v1 for an upstream AI investment research agent.

这两版都没有声称 human gold、neural reranking、production scale 或完整 answer quality。
