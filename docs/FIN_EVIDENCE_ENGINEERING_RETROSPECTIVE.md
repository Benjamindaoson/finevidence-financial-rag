
# FinEvidence 全生命周期技术复盘

> 本文不是 README、功能清单或 commit 罗列，而是基于 Git history、源代码、正式报告、实验 artifacts、OpenSpec、测试输出和项目知识库，重建 FinEvidence 如何从一个检索实验逐步演化为 Evidence-Qualified Retrieval Backend。

## 1. Executive Summary

FinEvidence 最初看起来像一个金融 RAG 项目：把财报、披露和表格送进检索系统，再让模型回答问题。但项目真正要解决的风险后来被重新定义了。

金融 RAG 最危险的错误不是明显报错，而是全链路都显示成功：解析成功、索引成功、检索成功、生成成功，但事实关系已经被破坏。系统可能找到语义相似的指标，却找错 period、entity、basis 或 document version；也可能只找到一个事实，却把它误认为足以回答一个需要多个独立 facts 的问题。

项目的演进主线是：

    提高 retrieval recall
          ↓
    发现受控夹具上的高分不等于真实金融有效
          ↓
    将 evidence completeness 与 hard-negative ranking 分开
          ↓
    发现 requirement understanding 是独立瓶颈
          ↓
    用 Requirement Graph 和 Independent Coverage 阻断假完整性
          ↓
    发现视觉不是默认答案，且 benchmark 本身可能有偏差
          ↓
    转向 failure diagnosis 与 structure-preserving TableIR
          ↓
    把已验证的证据能力冻结为 Evidence Backend v1

当前最可信的项目结论不是“做出了一个很强的多模态 RAG”，而是：

> 高风险金融系统不应该因为召回了相关内容就获得回答资格。系统至少要能说明问题需要哪些 evidence、每条 evidence 承担什么角色、关键需求是否被独立满足，以及引用是否可以回到确定的文档和页码。

项目当前可以证明：

- 相关性检索与证据充分性是不同问题。
- 在真实 TAT-QA/FinQA slice 上，Hybrid Retrieval 仍不能稳定找到完整 evidence set。
- Requirement Graph 能表达数值推导与多事实依赖。
- Independent Coverage 能识别同一 evidence 被复用导致的假完整性。
- 视觉检索在当前实验中是低召回、窄范围 fallback，不是主路径。
- 表格结构需要独立的 IR，Parsed Page Text 不能冒充 Structured Table IR。
- failure 需要先诊断，再决定是否升级到更昂贵的 modality。
- EvidenceObject/API 可以把这些底层能力以稳定边界交给上层 AI Investment Research Agent。

当前不能证明：

- FinRAGBench-V public page-image benchmark 已经完成。
- CLIP 视觉检索已经具备企业级金融能力。
- B3 已经 COMPLETE。
- TableIR semantic cell accuracy、merged-cell accuracy、footnote semantics 已经验证。
- Backend v1 已经是 production-scale、高可用或完整 ACL/ABAC 服务。
- 当前系统已经完成复杂投研 reasoning、冲突解决、版本管理或投资建议生成。

## 2. 我们最开始到底想解决什么

项目最初针对的是传统金融 RAG 的几个实际风险：

- 搜到语义相似但业务含义错误的 metric。
- 旧版本、错误地区或错误 entity 的数据击败当前有效数据。
- 一个答案需要多个 evidence，但系统只找到一个。
- PDF table 被 flatten 后丢失 row、column、header、unit 或 footnote 关系。
- 答案只存在于 chart、diagram 或页面空间关系中，OCR text 无法表达。
- 模型在证据不足时仍然生成看起来合理的答案。
- citation 指向正确页面，却不一定支持具体 claim。

例如：

    What was the percentage increase in revenue from 2023 to 2024?

这个问题至少需要：

    Revenue 2023
    Revenue 2024
    计算规则
    单位、currency 和 basis

而：

    Why did cost of risk increase?

还需要区分：

    当前 cost of risk
    前期 cost of risk
    观察到的变化
    管理层或风险披露解释

这些是不同 evidence roles，不能由一个 lexical-overlap 很高的 chunk 代替。

最初的工程直觉是：

    RAG = embedding + vector search + LLM

但真实实验把这个直觉拆开了：

- 受控 MiniBench 上高分，不能说明真实金融问题也能找全证据。
- RealFinance-v1 上 Dense Recall@5 只有 0.0900，Hybrid 只有 0.1417。
- Gold facts 已知时，bounded targeted retrieval 可以把 Final CER 提到 0.8900。
- 但 deterministic required-fact decomposer 的 Fact Recall 只有 0.0017。
- D3 Raw Self Coverage 可以达到 1.0000，却因为 evidence reuse 使 Independent CER 只有 0.7283。

因此项目逐渐从“提高 RAG retrieval”演化为“判断什么证据足够支持金融结论”。

## 3. 项目演进时间线

| 阶段 | 核心问题 | 实际工作 | 主要发现 |
|---|---|---|---|
| P0 初始切片 | 如何建立可复现的证据检索底座 | Evidence IR、MiniBench、CPU Dense/Hybrid | 先固定 document/page/block/score/hash |
| P0-B/P0-C | 完整证据和 hard negative 是否可测 | EvidenceCompleteness-v1、FinanceHardSet-v1 | 机制在受控夹具上有效，但不能代表真实数据 |
| P0-D | 受控结果能否迁移到真实金融 | RealFinance-v1：TAT-QA + FinQA | Recall 和 complete evidence 明显下降 |
| P0-E | 系统是否理解问题需要哪些 facts | D0–D3 decomposition | requirement understanding 是独立瓶颈 |
| P0-G | 如何阻断 evidence reuse inflation | Requirement Graph、alignment、Independent Coverage | 相关 evidence 不等于独立满足 requirement |
| P0-H | requirement 能否在 canonical subset 上验证 | RequirementAdjudicated-v1、HSBCNaturalHard-v1 | D4 改善了 representation，但 evidence mapping 仍弱 |
| B3 | 哪些 failure 真正需要 vision | page rendering、CLIP RN50、VisualStress | visual recall 低，fusion 没有自动变好 |
| B3.1 | 是否只在需要时调用视觉 | mixed routing、Recovery@K、latency | routing 可测，但未证明 cost saving |
| B3.2 | stress benchmark 是否有 construction bias | performance-blind audit、NaturalMultimodal control | stress set 偏向 text failure，自然集反而支持 text |
| B4 | 是否应该先诊断 failure | failure taxonomy、Oracle/E1 routing | capability 比 routing 更早成为瓶颈 |
| B4.1 | table failure 是否需要真实结构 | geometry-assisted TableIR、T2 executor | 结构可保留，但 semantic correctness 仍未知 |
| Backend v1 | 如何让上层 Agent 稳定调用 | EvidenceObject、FastAPI、coverage、verify、citation | 底层能力冻结成独立 HTTP boundary |

## 4. P0 初始阶段：先让 Evidence 可审计

最小 Evidence IR 保留：

    document_id
    page
    block_id
    bbox
    modality
    text
    table_id
    row_id
    column_id
    entity
    metric
    period
    retrieval_score
    rerank_score
    content_hash

Evidence 是 immutable Pydantic contract，content_hash 在 retrieval 前校验。这个设计决定了系统可以回答：

- 答案来自哪个 document？
- 位于哪一页、哪个 block？
- 这个内容在不同运行之间是否变化？
- parser 传给 retriever 的内容是否保持一致？

MiniBench-v1 是 30-question development/regression fixture，不是 FinRAGBench-V 或 ICBCBench score。早期结果：

    B0 tfidf_svd_dense Recall@5 = 0.7586
    B1 Hybrid Recall@5         = 0.7931

这些数字证明 runner、manifest、hash 和 trace 能工作，不证明真实金融泛化。

### P0-B/P0-C：把 ranking 与 completeness 分开

EvidenceCompleteness-v1 有 30 个 multi-fact cases；FinanceHardSet-v1 有 100 个 controlled hard-negative cases，覆盖 temporal、metric、related metric、entity、segment、basis、currency、geography、period type 和 table context。

在受控 fixture 上：

    Hybrid + Financial Facets
    Recall@5 = 1.0000
    MRR       = 1.0000
    nDCG@10   = 1.0000
    HN Error  = 0.0000

EvidenceCompleteness-v1 上：

    Initial CER                   = 0.0000
    Final CER                     = 1.0000
    Partial-to-Complete Recovery  = 1.0000
    False Answer Eligibility Rate = 0.0000

这证明了两个机制在已知夹具上可以工作：

1. financial facets 可以区分被设计出来的 hard negatives；
2. 如果系统已经知道缺少哪个 fact，bounded targeted retrieval 可以找回夹具中的 evidence。

但这组结果也暴露了风险：query、candidate 和 facet 都被人工控制。它不能回答真实金融文档里的 parser corruption、表格关系、版本冲突、单位错误和分散证据问题。

这一步把项目从一个单一 retrieval score 拆成：

    Ranking quality
    Evidence completeness

一个候选可以排名第一，但仍然不够回答；一个问题也可能需要继续检索，而不是立即生成。

## 5. P0-D：真实金融数据把漂亮结果打回原形

RealFinance-v1 是冻结的 public-source-derived slice：

    100 cases
    50 TAT-QA table-text
    50 FinQA answerable development records
    1,652 Evidence IR items

TAT-QA 和 FinQA 的 source commits、raw file hashes、derived manifest、gold_inds、program 和 execution answer 都保留，原始 benchmark 没有被修改。

### 结果

| System | Recall@5 | MRR | nDCG@10 | Complete Evidence |
|---|---:|---:|---:|---:|
| Dense | 0.0900 | 0.1027 | 0.0773 | 0.0300 |
| Hybrid + Generic | 0.1417 | 0.1895 | 0.1405 | 0.0500 |
| Facet-aware / predicted facets | 0.1417 | 0.1912 | 0.1398 | 0.0500 |

Gold required facts 下：

    Initial CER  = 0.0300
    Final CER    = 0.8900
    Recovery     ≈ 0.8866

Deterministic required-fact understanding：

    Fact Precision = 0.0100
    Fact Recall    = 0.0017

这两个结果必须一起看：

- 假设系统已经知道真正需要哪些 facts，targeted retrieval 还有很大恢复空间。
- 但系统自己的 decomposer 几乎不能恢复 gold facts。
- 因此“后续检索做得不错”不能掩盖“前面没有定义清楚需要什么”。

P0-D 的 Top-K RAG FAER 为 0.1200；Coverage Gate 和 Targeted Retrieval 的 FAER 为 0.0000。这个结果的准确解释是：显式资格门阻止了部分缺少完整 evidence 的回答资格，而不是宣称 answer accuracy 已经解决。

### 技术判断

低 Recall 不能简单归因于 embedding 不够强。更符合代码和 trace 的解释是：

1. 真实 table-text context 比 MiniBench 更长、更松散。
2. supporting evidence 分散在多个 table row、paragraph 或 page。
3. 自然问题不直接给出 canonical entity、metric 和 period。
4. lexical retrieval 只能找相似文本，不能决定 evidence set 是否完整。
5. decomposer 没有拆出 fact，retrieval 就没有明确目标。

因此下一阶段进入 Requirement Understanding，而不是只换更强 embedding。

## 6. P0-E：真正的瓶颈不是简单 Retrieval

P0-E 把链路拆为：

    Question → Required Facts → Evidence Mapping → Coverage

比较：

    D0 Heuristic
    D1 LLM Direct
    D2 Schema-constrained
    D3 Evidence-aware

D1 因没有授权 provider 保持 N/A；TAT-QA/FinQA 没有 canonical entity/metric/period/role/criticality labels，所以 slot metrics 也保持 N/A。

P0-E 最重要的发现是：

    D3 Predicted CER = 1.0000

这个结果初看像成功，随后却发现多个 predicted facts 被同一个 candidate evidence 重复覆盖。系统评价的是“自己定义的 fact list 是否有 lexical overlap”，而不是“是否识别出真实问题需要的不同事实”。

这次失败产生了 P0-G。

## 7. P0-G：第一次把“相关”与“足够”分开

P0-G 的核心原则：

> A relevant evidence item is not sufficient for answer eligibility.

### Requirement Graph

系统用 Python/Pydantic DAG 表示：

    R1 current value       RETRIEVED_FACT  CRITICAL
    R2 prior value         RETRIEVED_FACT  CRITICAL
    R3 observed change     DERIVED_FACT    CRITICAL
       depends_on = [R1, R2]

R3 不要求文档中出现字面上的最终 change。它通过 R1、R2 的独立覆盖和合法 operation 得到满足。

Schema 支持：

    RETRIEVED_FACT
    DERIVED_FACT
    EXPLANATORY_FACT
    CONTEXT_FACT

以及：

    CRITICAL
    SUPPORTING
    OPTIONAL

还支持 role、entity、metric、period、segment、basis、geography、currency、unit、operation、depends_on 和 acceptable evidence IDs。

### Alignment 与 Reuse Policy

每个 requirement/evidence pair 都产生：

    support_type
    alignment_score
    matched_slots
    mismatched_slots
    reusable
    reason

EvidenceReusePolicy 不允许 evidence 无条件覆盖多个不同语义角色。当 role、period、metric、entity 等关键 slots 不兼容时，会产生 EVIDENCE_REUSE_INFLATION，并从 independent coverage 中排除。

### P0-G 结果

| Method | Raw Self Coverage | Independent CER | Critical Coverage | Invalid Reuse Rate | FAER |
|---|---:|---:|---:|---:|---:|
| Gold evidence condition | N/A | 0.9083 | 0.9083 | N/A | 0.0000 |
| D0 Heuristic | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| D2 Schema-constrained | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| D3 Evidence-aware | 1.0000 | 0.7283 | 0.7400 | 0.4100 | 0.4100 |
| D4 Requirement-Graph-Constrained | 0.6133 | 0.5033 | 0.5050 | 0.3600 | 0.0000 |

D3 的核心 acceptance result：

    Raw Self Coverage  = 1.0000
    Independent CER    = 0.7283
    Critical Coverage  = 0.7400
    Invalid Reuse Rate = 0.4100
    FAER               = 0.4100

这不是质量提升，而是证明系统能把“看起来全覆盖”的结果降级为不具备完整回答资格。

D4 没有在 100-case public slice 上改善 D3：

    Independent CER   = 0.5033
    Critical Coverage = 0.5050

这个负结果保留。Graph structure 可以更准确表达“缺什么”，但不会自动找到缺失输入。

## 8. P0-H：不用伪造 Human Gold

P0-H 从 RealFinance-v1 建立 36-case RequirementAdjudicated-v1：

| Question type | Cases |
|---|---:|
| factual | 10 |
| comparison | 4 |
| numerical | 18 |
| trend | 3 |
| explanation | 1 |
| multi-document synthesis | 0 |

流程是：

    Pass A 独立 annotation
    Pass B 独立 annotation
    Adjudication 基于 question、supporting evidence、gold answer/program

但没有真实人类逐条确认，因此严格标记：

    annotation_method = dual_pass_model_assisted_adjudication
    human_verified    = false

它不能称为 human gold、expert gold 或 TAT-QA/FinQA 官方 requirement gold。

### Annotation agreement

| Dimension | Agreement |
|---|---:|
| Requirement count | 1.0000 |
| Question type | 1.0000 |
| Fact type | 0.7222 |
| Criticality | 0.7222 |
| Role | 0.7222 |
| Dependency | 0.7222 |
| Evidence mapping | 0.2315 |

Evidence mapping agreement 只有 0.2315，证明“知道问题需要一个事实”和“知道哪个 block 真正支持该事实”是两个不同难度的问题。

### D0–D4

| Method | Req Precision | Req Recall | Critical Recall | Type Acc | Role Acc | Dependency Acc | Count Error | Independent CER | Critical Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| D0 Heuristic | 0.0000 | 0.0000 | 0.0000 | 1.0000 | N/A | N/A | 1.3056 | 0.0000 | 0.0000 |
| D1 LLM Direct | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| D2 Schema-constrained | 0.2778 | 0.2778 | 0.2778 | 1.0000 | 1.0000 | N/A | 0.0278 | 0.0000 | 0.0000 |
| D3 Evidence-aware | 0.2778 | 0.2778 | 0.2778 | 1.0000 | 1.0000 | N/A | 0.0278 | 0.0000 | 0.0000 |
| D4 Requirement Graph | 0.7222 | 0.7222 | 0.7222 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.3704 | 0.3750 |

D4 在这个 adjudicated subset 上优于 D0/D2，但有两个限制：

1. adjudicated graph 使用了与 D4 类似的 question-type templates，存在 annotation ceiling；
2. D4 Independent CER 仍只有 0.3704，Critical Coverage 只有 0.3750。

D1 使用本地 SmolLM2-135M-Instruct、Transformers CPU、greedy decoding，实际加载和生成过 output，但 36/36 无法通过 JSON schema：

    D1 = N/A
    reason = MALFORMED_LLM_JSON

这属于 model/runtime/schema integration failure，不能当成合格的 decomposition quality score。

### HSBCNaturalHard-v1

P0-H 固定了官方 HSBC FY2025 corpus：

| Document | Pages | SHA-256 |
|---|---:|---|
| FY2025 Annual Report | 372 | 94aab2f5c83d1060ee95d344f1915833869fe4502dc635e4ab9ca84f496ee94b |
| FY2025 Pillar 3 | 122 | eb64c8f0fcd32648512979886bceddba7128558761c07948b50f6ecfa83a32f7 |

从真实 parsed page blocks 中保留 59 个 valid cases。一个候选没有通过 hard-case quality gate，因此没有为了凑 60 个手工保留。

| System | Recall@5 | MRR | nDCG@10 | HN Error | Top-1 Positive |
|---|---:|---:|---:|---:|---:|
| Dense | 0.1864 | 0.1312 | 0.1290 | 0.3898 | 0.0847 |
| Hybrid + Generic | 0.2881 | 0.2322 | 0.3364 | 0.3898 | 0.0847 |
| + Predicted Facets | 0.9661 | 0.7759 | 0.8313 | 0.0339 | 0.6441 |
| + Adjudicated Facets | 0.9661 | 0.7759 | 0.8313 | 0.0339 | 0.6441 |

Ranking Oracle Gap 为 0.0000。它说明这个 set 没有暴露 predicted facet extraction bottleneck，而不是说明企业级 facet extraction 已经解决；因为 queries 是从 facet-bearing positive pages 中挖出的，存在 selection effect。

## 9. B3：我们以为视觉会解决问题

B3 的研究问题：

> 哪些 critical financial evidence failures 真正需要 vision？能否避免所有 query 都支付 multimodal cost？

### 数据和模型

- HSBC FY2025 Annual Report：372 pages。
- HSBC FY2025 Pillar 3：122 pages。
- deterministic 72-DPI rendering：494 page images。
- OpenAI CLIP RN50，CPU。
- visual query encoding 实际读取 rendered page images，不是 OCR text embedding 改名。
- CUDA unavailable，没有 GPU-seconds 或 monetary cost claim。

HSBCVisualStress-v1 有 60 个 project-created cases，来自真实 page/block，覆盖 table、header、unit、footnote、chart、caption、multi-column、layout 等类别。B3.2 后确认它不能作为自然问题 benchmark。

### Page retrieval

| System | Page R@1 | Page R@5 | Page R@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| T0 Text Only | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| T1 Parsed Page Text | 0.0000 | 0.0000 | 0.0333 | 0.0044 | 0.0108 |
| V0 Visual Only | 0.0167 | 0.0500 | 0.1000 | 0.0303 | 0.0459 |
| M0 Fusion RRF | 0.0167 | 0.0167 | 0.0500 | 0.0209 | 0.0272 |
| M0 Fusion Weighted | 0.0167 | 0.0167 | 0.0500 | 0.0200 | 0.0263 |
| M1 Conditional Multimodal | 0.0167 | 0.0167 | 0.0500 | 0.0209 | 0.0272 |

B3 没有证明视觉能普遍改善 retrieval。技术上可能的原因是：

1. 整页 embedding 与局部 claim 缺少区域对齐。
2. table 问题需要 row/column/header/unit 关系，不只是视觉主题相似度。
3. 长文档有大量相似页面，主题相似不等于 evidence 正确。
4. visual candidate 不能自动补回 requirement semantics。

### Recovery

| Metric | Result |
|---|---:|
| Text Failure Recovery@10 | 3/60 = 0.0500 |
| Visual Critical Requirement Recovery@10 | 0.0500 |
| Multimodal Regression@10 | 0.0000 |
| Net Recovery@10 | +3 |
| Visual Invocation Rate | 1.0000 |
| Unnecessary Invocation Rate | 1.0000 |

这里必须保留 @10。早期无 cutoff 的“3/60”容易歧义，B3.1 后改为 Recovery@1/@5/@10。

## 10. B3.1：从 Always-on Multimodal 转向 Conditional Escalation

HSBCMultimodalRouting-v1：

    TEXT_SUFFICIENT          10
    TABLE_PARSED_SUFFICIENT  10
    VISUAL_NEEDED            10

Router 只接收 question、parser confidence 和 observed coverage，不读取 gold modality。

结果：

    Routing precision              = 10/23 = 0.4348
    Routing recall                 = 10/10 = 1.0000
    Visual invocation rate         = 23/30 = 0.7667
    Unnecessary invocation rate    = 13/20 = 0.6500
    Critical recovery              = 2/17 = 0.1176
    Multimodal regression          = 0/30 = 0.0000
    Net recovery                   = +2

这个结果说明 conditional routing 可以测量，但没有证明 cost saving：

- 所有 VISUAL_NEEDED 都路由到视觉。
- 9/10 TABLE_PARSED_SUFFICIENT 被错误升级到视觉。
- 4/10 TEXT_SUFFICIENT 也被升级到视觉。
- 非视觉 cases 中 unnecessary invocation 为 65%。

组件 latency：

| Component | P50 ms | P95 ms |
|---|---:|---:|
| Text retrieval | 208.78 | 222.85 |
| Parsed-page retrieval | 208.22 | 222.21 |
| Visual query encoding/retrieval | 71.09 | 77.42 |
| Fusion | 0.12 | 0.14 |
| Routing | 0.03 | 0.05 |
| Evidence qualification | 6.22 | 7.61 |
| End-to-end | 502.07 | 528.96 |

Offline indexing 与 query latency 分开记录。CPU 本地 timing 不能直接换算成生产价格。

## 11. B3.2：Benchmark 反噬，以及为什么这是好事

B3.2 performance-blind audit 专门检查 T0 Recall@10 = 0/60。

VisualStress-v1 的事实是：

- 60 cases 只来自 10 个固定 question templates。
- 每个 template 重复 6 次。
- positive page 通过 keyword occurrence 选择。
- selection 本身天然制造了 text retrieval failure。

T0 在 @50 找回 7/60，因此 @10=0/60 是可复现观察值，但不能解释成自然金融问题的无偏 text baseline。

固定 20-case attribution：

    TABLE_STRUCTURE_LOSS  8
    CHART_VISUAL_ONLY     8
    PAGE_FRAGMENTATION    2
    LAYOUT_DEPENDENCY     2

随后建立 performance-blind、排除 stress candidate pages 的 HSBCNaturalMultimodal-v1：

    80 real HSBC page cases
    Annual Report 40
    Pillar 3 40

Natural @10：

| System | Recall@10 |
|---|---:|
| T0 Text Only | 0.5375 |
| T1 Parsed Page Text | 0.5875 |
| V0 Visual Only | 0.0750 |
| M1 Conditional | 0.5625 |

结论发生了反转：benchmark 质量提高后，text/parsed text 比 visual 更强。这不是项目失败，而是获得了更可信的结论：

> 视觉应是针对 chart、layout 和 visual-only evidence 的窄路径 fallback，而不是所有金融 query 的默认路径。

FinRAGBench-V 仍然没有完成 public page-image evaluation。revision、queries、qrels 都固定，但 2.378GB archive 在 Hugging Face/Xet 和 WSL wget bounded attempt 中都没有完成；partial archive 没有被使用，metadata hit 没有被冒充成 page-image score。

## 12. B4：从 Modality Routing 转向 Failure Diagnosis

B4 的核心问题变成：

    当前证据为什么失败？

而不只是：

    这个 query 用 Text 还是 Vision？

failure taxonomy 包括：

    TABLE_STRUCTURE_LOSS
    MULTI_LEVEL_HEADER
    UNIT_HEADER_LOSS
    CHART_VISUAL_ONLY
    PAGE_FRAGMENTATION
    LAYOUT_DEPENDENCY
    TEXT_EXTRACTION_CORRUPTION

比较：

- E0 Oracle route：使用 gold failure category 测 headroom，只能是 evaluation oracle。
- E1 predicted route：只使用 question、initial coverage、parser capability 等运行时可得信号。

E1 结果：

    route accuracy             = 0.5000
    visual invocation          = 0.5000
    Predicted Failure R@10     = 0.0833
    critical recovery          = 0.0833
    regression                 = 0.0000

关键判断是：

> 最大瓶颈从 Routing 转移到了 Capability。

知道“这是 table failure”不够；如果下游没有真正能消费 row、column、header、unit 的 executor，正确路由也不会带来恢复。

## 13. B4.1：从 Page Text 到真正的 TableIR

B4.1 通过以下步骤处理真实 HSBC FY2025 Annual Report pages 1–26：

    pdfplumber positioned words
    table-like region detection
    row grouping
    numeric-column clustering

TableIR 保留：

    table_id
    row_id
    column_id
    header path
    value
    unit/period when present
    bbox
    document/page provenance

E0 structure results：

    Accepted table-like regions   = 24
    Pages with accepted regions   = 13
    Structure recoverable rate    = 0.7418
    Header path population        = 0.7278
    Cell identity invariant       = 1.0000
    Row/column relation invariant = 1.0000

以下仍然是 N/A：

    Semantic cell accuracy
    Unit association accuracy
    Merged-cell accuracy
    Footnote semantics

原因是没有 verified human TableIR gold。Table parse success=1.0000 只表示 accepted region 都产出了 TableIR，不表示语义恢复正确。

T2 Real Structured Table IR executor：

    T2 R@1  = 0.0167
    T2 R@5  = 0.0833
    T2 R@10 = 0.0833

在 24 个 table-category failures 中，相对 T1：

    Page recovery@10       = 5/24
    Critical qualification = 4/24
    Regression             = 0

这是有限但真实的恢复，不是“已经解决金融表格理解”。T2 仍受 page scope、candidate cell crowding、parser coverage 和 semantic gold 缺失影响。

### 为什么 T2 + Text RRF 没有更好

T2 单独在 @10 恢复 5 个 table pages，T2+Text RRF 只恢复 4 个；V0 同一 cutoff 为 0.1000。

这说明：

    Fusion ≠ automatic complementarity

如果候选空间没有互补，RRF 会把 table candidate 和 text noise 混合，成为 reranking noise。fusion 必须通过 candidate diversity、score calibration、coverage 和 ablation 证明，而不是因为算法名字叫 RRF 就假定会提升。

## 14. Evidence Backend v1：从研究代码到可复用基础设施

B4.1 后继续往底层塞 Agent、投研逻辑和更多 benchmark，边际收益已经下降。因此项目冻结为独立 Evidence Backend v1。

最终边界：

    Financial documents
          ↓
    Parsing / page rendering / TableIR
          ↓
    Evidence IR
          ↓
    Text / table / visual retrieval
          ↓
    Fact–evidence alignment
          ↓
    Independent / critical coverage
          ↓
    Verification / citation
          ↓
    Evidence Backend API
          ↓
    AI Investment Research Agent

### EvidenceObject

外部调用者不直接依赖内部 Evidence、retriever、parser、CLIP 或 benchmark classes，而是获得版本化 EvidenceObject，分为：

    identity
    provenance
    content
    financial metadata
    structure
    verification

保留的关键字段：

    evidence_id
    document_id
    source_type
    score
    text/table/visual_reference
    document_name
    page_number
    source_url
    document_hash
    entity/metric/period
    table_id/row_id/column_id
    bbox
    coverage_status

### API 的工程含义

| Endpoint | 解决的边界 |
|---|---|
| GET /health | 确认服务和 evidence catalog 是否可用 |
| POST /api/v1/evidence/search | 给上层 Agent 找到带 provenance 的 evidence |
| POST /api/v1/evidence/coverage | 判断 requirements 是否独立满足 |
| POST /api/v1/table/query | 对已有 table evidence 做 metadata-first lookup |
| POST /api/v1/evidence/verify | 对单个 claim 复用 coverage 资格门 |
| GET /api/v1/evidence/{id}/citation | 将 evidence ID 解析为 document/page/table/row/column/bbox |

当前 API 使用 in-memory CPU HybridRetriever，适合本地 integration，不是规模、可用性或生产成本承诺。

真实本地 HTTP smoke：

    GET /health = 200
    catalog_size = 984

没有本地 HSBC artifacts 时，服务会诚实返回 catalog_size=0，不会制造 evidence。

上层 Agent 不需要知道 CLIP 或 pdfplumber，只依赖 EvidenceObject 和 API contract：

    Question
       ↓
    Requirement decomposition
       ↓
    /evidence/search
       ↓
    保留 evidence_id
       ↓
    /evidence/coverage
       ├── ELIGIBLE → verify → citation → grounded memo
       ├── PARTIAL  → missing requirements → targeted retrieval
       └── INSUFFICIENT → narrow question or abstain

## 15. 从差到好的指标演进

### 15.1 受控 Recall 到真实 Recall

    MiniBench B0 Recall@5                = 0.7586
    MiniBench B1 Hybrid Recall@5          = 0.7931
    FinanceHardSet Hybrid R@5             = 1.0000
    RealFinance Dense R@5                 = 0.0900
    RealFinance Hybrid R@5                = 0.1417

不是项目退步，而是数据从受控 fixture 进入真实 financial source slice 后，指标开始测到真实困难。

### 15.2 Self-coverage 到 Independent Coverage

    D3 Raw Self Coverage = 1.0000
    D3 Independent CER   = 0.7283
    D3 Critical Coverage = 0.7400
    Invalid Reuse Rate   = 0.4100

这里的下降是 safety gate 发现错误，不是系统质量变差。

### 15.3 Gold evidence recovery 到 requirement understanding

    Gold facts + targeted retrieval Final CER = 0.8900
    Deterministic fact recall                = 0.0017

系统必须同时优化“找 evidence”和“知道要找什么”。

### 15.4 VisualStress 到 NaturalMultimodal

    VisualStress T0 @10       = 0.0000
    VisualStress V0 @10       = 0.1000
    Natural T0 @10            = 0.5375
    Natural T1 @10            = 0.5875
    Natural V0 @10            = 0.0750
    Natural M1 @10            = 0.5625

更可信的 benchmark 让视觉优势叙事消失，但让最终工程判断更可靠。

### 15.5 Parsed Text 到 TableIR

    T1 = Parsed Page Text
    T2 = Real Structured Table IR executor

T2 的 structure invariant 为 1.0000，但 semantic cell accuracy 仍为 N/A。它证明可寻址结构基础，不证明理解已经完成。

## 16. 最重要的失败案例与技术判断

### 失败 1：受控夹具上的 100% recovery

现象：EvidenceCompleteness-v1 targeted retrieval recovery=1.0000。

判断：机制在已知夹具中有效，但 query 和 evidence 太可控。

验证：迁移到 RealFinance-v1 后 Hybrid R@5=0.1417，Gold Final CER=0.8900。

学习：所有 1.0 都必须用外部真实数据复核。

### 失败 2：D1 local LLM 36/36 malformed JSON

现象：模型加载并生成，但没有 output 通过 schema。

原因判断：本地 SmolLM2-135M 与严格 decomposition contract 不匹配。

处理：保留 D1=N/A / MALFORMED_LLM_JSON，不用 heuristic 替代。

学习：模型调用成功不等于协议成功。

### 失败 3：D3 Raw Self Coverage 假完美

现象：D3 self-coverage=1.0000。

原因：同一 evidence 被 lexical overlap 复用于多个不等价 facts。

处理：EvidenceReusePolicy、invalid reuse event、Independent Coverage。

学习：coverage 必须同时依赖 requirement set、role 和独立性。

### 失败 4：CLIP visual retrieval 很弱

现象：VisualStress V0 R@10=0.1000，Fusion 没优于 V0。

原因判断：整页 image embedding 与局部金融 evidence 缺少对齐。

处理：视觉降级为窄路径，并继续经过 Evidence Qualification。

学习：CLIP page retrieval 不能写成 VLM understanding。

### 失败 5：Routing invocation 过高

现象：mixed routing visual invocation=76.67%，unnecessary=65.0%。

原因：coverage failure 不等于 visual-needed；table capability 和 failure classifier 都不完整。

处理：B4 引入 failure diagnosis 与 capability boundary。

学习：router recall 高不代表 cost saving。

### 失败 6：VisualStress construction bias

现象：T0 @10=0/60。

原因：10 个固定模板重复六次，positive page 用 keyword occurrence 选择。

处理：performance-blind audit + NaturalMultimodal control。

学习：benchmark integrity 是实验结果的一部分。

### 失败 7：Oracle route 仍不够

现象：Oracle route 有 headroom，但整体恢复仍有限。

原因：知道 failure type 不会凭空创造 executor。

处理：B4.1 建立真实 TableIR executor。

学习：routing 是决策层，capability 才是恢复层。

### 失败 8：Structure invariant 被误读成 semantic accuracy

现象：cell identity/row-column invariant=1.0000。

错误说法：TableIR 理解准确率=1.0。

正确说法：结构对象保持 identity 和 relation；semantic/unit/merged/footnote gold 仍 N/A。

### 失败 9：T2 + Text RRF 反而下降

现象：T2 @10 恢复 5 个 table pages，fusion 只恢复 4 个。

原因：候选空间没有证明互补，text noise 改变排序。

学习：RRF 是组合机制，不是质量保证。

### 失败 10：FinRAGBench-V archive blocker

现象：2.378GB pinned archive 多次下载未完成。

处理：固定 revision/query/qrels，保留 Xet/HTTP/WSL blocker evidence，不使用 partial archive。

学习：外部依赖失败时保持 N/A 比填一个不可审计的分数更有价值。

### 失败 11：Docker Hub blocker

现象：docker compose config 通过，但 docker build 在 auth.docker.io token 请求处失败。

判断：外部基础镜像网络问题，不是 Python API 代码错误。

处理：保留 Dockerfile/.dockerignore，报告 build blocker，不伪造 success。

学习：package validity、image build 和 runtime smoke 是三种不同证据。

## 17. 最终架构为什么这样设计

每一层都对应一个已暴露的 failure：

    Financial Document
          ↓  防止 source identity 丢失
    Document / Page / Table Parsing
          ↓  防止 reading order / row / column 被 flatten
    Text / Table / Visual Retrieval
          ↓  找候选，但不授予回答资格
    EvidenceObject
          ↓  固定 identity + provenance + structure
    Fact–Evidence Alignment
          ↓  判断 evidence 是否支持 role/slot
    Independent / Critical Coverage
          ↓  阻断 reuse inflation 和缺关键事实
    Verification / Citation
          ↓  claim → evidence → page/document/hash
    Evidence Backend API
          ↓  对上层 Agent 隔离内部实现
    AI Investment Research Analyst

没有选择 PDF→LLM，因为 parser 可能已经破坏结构，模型只能在错误 representation 上生成。

没有选择所有页面都走 VLM，因为 visual recall 低，且 invocation、latency、model cost 必须被单独测量。

没有选择所有问题都走 Agent，因为 bounded deterministic targeted retrieval 已足够验证 evidence mechanism；Agent 数量不会自动解决 mapping 或 coverage。

没有选择 blind fusion，因为 T2+Text 的负结果表明，候选空间没有互补时 fusion 会引入 noise。

没有把 evaluation runner 直接当 service，因为外部 Agent 需要稳定 contract，而不是知道 p0_g.py、CLIP adapter 或内部 benchmark class。

## 18. 项目真正的技术亮点

### 1. Evidence-first，而不是 answer-first

把 answer eligibility 放在 generation 之前，保留 missing critical requirements。

### 2. Independent Coverage 阻断假完整性

将 Raw Self Coverage 与 Independent CER 分开，识别一个 evidence 被错误复用多个 role。

### 3. Failure-aware Retrieval

不把所有失败都归因于 embedding，而是区分 requirement miss、table structure loss、visual-only information、page fragmentation 和 capability gap。

### 4. Benchmark integrity 进入工程闭环

VisualStress 的 construction bias 被审计并保留，NaturalMultimodal 作为独立 control 产生更可信的反向结论。

### 5. Structure-preserving TableIR

不再把 Parsed Page Text 冒充 Structured Table IR，保留 table/row/column/bbox/provenance，并对未验证 semantic fields 使用 N/A。

### 6. Provenance 和 citation 是数据模型的一部分

document hash、page、source URL、table identity、row/column 和 bbox 不是报告末尾补的字段，而是 EvidenceObject contract。

### 7. 稳定 Backend boundary

FastAPI v1 让 AI Investment Research Agent 能调用 search、coverage、verify、citation，而无需复制 parser、retriever、CLIP 或 benchmark code。

## 19. 当前缺点：技术债与合理边界

### 真正的技术债

- deterministic alignment 主要是 lexical/slot logic，不是 neural entailment verifier。
- evidence mapping agreement 只有 0.2315。
- local D1 没有通过 JSON contract。
- HSBC TableIR 缺少 verified human semantic gold。
- visual retrieval 缺少 region-level model、region gold 和更强 page-to-claim alignment。
- FinRAGBench-V public page-image track 未闭环。
- Backend v1 使用 in-memory CPU retrieval，没有持久化、scale、SLA 或完整 auth。
- 尚未与真实 AI Investment Analyst 端到端接通。
- conflict resolution、document version supersession、cross-document multi-hop 仍是后续能力。

### 合理的 scope boundary

- 没有加入 GraphRAG/Neo4j，因为当前 graph 是 evidence requirement DAG，不是知识图谱。
- 没有加入 multi-agent，因为当前首要问题是 evidence contract 和 qualification，不是 Agent 数量。
- 没有加入 Kubernetes/复杂 serving，因为 retrieval quality 和 capability 尚未证明值得扩展部署。
- 没有把没有 human verification 的 annotation 叫 expert gold。
- 没有把 project-created stress score 叫 public benchmark score。

## 20. 如果重新做一次

1. 更早建立小型、真实、人工确认的 requirement/evidence alignment subset。
2. 在引入视觉之前就冻结无偏的 natural page-level control set。
3. 更早建立 capability matrix，明确哪些 failure 由 text、TableIR、visual、calculation 或 abstention 处理。
4. 从第一天分层记录 page、block、cell 和 claim citation。
5. D1 先通过小型 schema smoke，再进入正式矩阵。
6. 把 public benchmark transport availability 作为预注册 gate。
7. Backend v1 应尽早存在，但保持薄，只提供 EvidenceObject、coverage、verify、citation；calculation、thesis、memory 放在上层 Investment Analyst。

## 21. 面试讲法

### 30 秒版

我做的不是一个“搜到文档就让 LLM 回答”的金融 RAG，而是一套 evidence-qualified retrieval system。项目先在受控夹具上验证 completeness 和 financial hard-negative ranking，随后迁移到 TAT-QA、FinQA 和真实 HSBC 披露，发现真实瓶颈不是单纯 embedding，而是 requirement decomposition、evidence mapping、表格结构和 benchmark bias。后来我用 Requirement Graph、Independent Coverage、failure-aware routing 和结构保持的 TableIR 把这些问题拆开，最后把可验证的 retrieval、coverage、verify、citation 能力冻结成 Evidence Backend v1，供上层 AI 投研 Agent 调用。

### 2 分钟版

最初我们想提高金融 RAG 的 retrieval，但受控 MiniBench 和 hard-negative 上的高分很快产生了错觉。到了 RealFinance-v1，Dense Recall@5 只有 0.09，Hybrid 也只有 0.1417，complete evidence 更低。Gold facts 已知时 targeted retrieval Final CER 是 0.89，可 deterministic fact recall 只有 0.0017，所以我们把 retrieval miss 和 requirement miss 分开。

P0-G 是关键转折。我们把问题表示成 requirement graph，区分 retrieved fact、derived fact 和 explanatory fact。一个 derived fact 通过依赖满足，不要求 chunk 中出现最终结果。每个 requirement/evidence pair 都要 alignment，再用 reuse policy 检查独立性。D3 raw self coverage 1.0 降为 independent 0.7283、critical 0.74，invalid reuse 0.41。这是 safety finding，不是 accuracy improvement。

随后做多模态实验。CLIP RN50 真的读取 rendered page images，但 VisualStress 的 visual recall 很低，Fusion 也没有稳定提升。B3.2 又发现 VisualStress 有固定模板和 keyword positive selection。Natural control @10 是 T0 0.5375、T1 0.5875，而 V0 只有 0.075。最终结论不是视觉普遍更强，而是视觉是诊断后的窄路径。

B4 证明 capability 比 routing 更关键；B4.1 建立真实 TableIR，structure invariant 为 1.0，但 semantic accuracy 仍为 N/A。最终我们把 evidence、coverage、verify 和 citation 封装成 Backend v1，让上层 Agent 只依赖稳定契约。

### 5 分钟深挖版

面试深挖时按“假设—实验—失败—架构改变”讲。

第一，金融 RAG 的错误经常是可信的错误。旧版文档、相似 metric、不同 period、表格 row/column、脚注和解释性文本会让系统拿到语义相似但业务含义不对的 chunk。一个问题需要 evidence set，不是一个 top-1。

第二，受控 fixture 的高分必须外部验证。MiniBench 和 FinanceHardSet 机制结果很高，但 RealFinance-v1 将 Dense/Hybrid Recall@5 拉到 0.09/0.1417。Gold facts 已知时 targeted retrieval Final CER=0.89，但 deterministic fact recall=0.0017，因此把 retrieval miss 与 requirement miss 分开。

第三，P0-G 把问题变成 requirement graph。区分 retrieved、derived、explanatory facts，显式依赖和 criticality。D3 raw self coverage=1.0 降为 independent=0.7283、critical=0.74，invalid reuse=0.41。这个下降是 gate 发现假完整性。

第四，视觉实验没有得到预设答案。CLIP RN50 实际读取 rendered page image，但 VisualStress @10 V0=0.10、Fusion=0.05。B3.2 发现 benchmark construction bias；Natural control 上 T0/T1=0.5375/0.5875、V0=0.075。结论变成 visual fallback，而不是 visual default。

第五，B4/B4.1 暴露 capability gap。知道是 table failure 不等于有 TableIR executor。B4.1 在 24 regions、13 pages 上得到 structure recoverable rate=0.7418，identity/row-column invariant=1.0，但 semantic fields N/A；T2 @10=0.0833，table category recovery=5/24，说明有限恢复而不是 table understanding solved。

最后是边界：FinEvidence Backend v1 提供 EvidenceObject、search、coverage、table query、verify、citation。AI Investment Analyst 做 mandate、plan、calculation、hypothesis、thesis 和 memo；底座负责“证据是否可追踪、是否支持 requirement、是否获得回答资格”。

## 22. 面试官可能追问的问题与回答

### 1. 为什么不用 VLM 直接处理所有 PDF？

因为实验没有证明视觉是普遍收益。整页 visual retrieval recall 低，NaturalMultimodal 上 text 更强；所有页面走 VLM 还会叠加 parser、视觉编码、reranking 和 generation cost。合理策略是先用便宜路径诊断 failure，再只对 chart、layout、visual-only evidence 升级。

### 2. 为什么 CLIP 失败？

这里的“失败”指当前 page-level retrieval recall 低，不是全面否定 CLIP。query 与整页 image embedding 缺少局部 claim alignment，金融表格还需要 row、column、header、unit 关系。结果只能支持窄范围 visual fallback，不能支持 VLM reasoning claim。

### 3. 为什么不用 LayoutLM？

项目没有实际运行 LayoutLM，不能把它写成实验结果。先固定真实任务、structure IR、region/cell gold，再比较模型；否则只是模型名替换。

### 4. TableIR 怎么处理 merged cells？

当前 B4.1 保留 table、row、column、header、bbox identity，但没有 verified merged-cell semantic gold，所以 merged-cell accuracy 是 N/A。parser 产出结构对象不等于 merged semantics 正确。

### 5. 为什么 RRF 反而下降？

T2+Text 候选空间没有被证明互补。T2 单独 @10 恢复 5 个 table pages，fusion 只恢复 4 个，说明 text noise 改变了排序。RRF 解决 rank combination，不解决 candidate quality、modality complementarity 或 evidence qualification。

### 6. 如何定义 Evidence Sufficiency？

先把问题拆成 typed requirements，再检查所有 critical requirements 是否由 role-correct、slot-compatible、独立 evidence 或合法 derived dependency 支持。相关 chunk 数量不是 sufficiency，Raw Self Coverage 也不是 sufficiency。

### 7. 为什么 Oracle routing 仍然不高？

Oracle 只告诉系统 failure type，不会创造下游 capability。知道是 table failure，但没有能消费 row/column 的 executor，仍然无法恢复。

### 8. 如何判断 benchmark construction bias？

在读取模型结果之前冻结 selection manifest，检查 template repetition、positive selection rule、candidate provenance、lexical overlap 和不同 cutoff。VisualStress 的固定模板、keyword page selection 和 @50 高于 @10 共同支持 bias 判断。

### 9. 为什么不直接用 GraphRAG？

当前 graph 表示回答问题需要哪些 evidence，是 requirement DAG，不是实体知识图谱。Neo4j 不会自动修复 parser corruption、evidence entailment 或 critical coverage。

### 10. 如何避免 citation 指向正确页面却支持错误 claim？

绑定 claim → evidence_id → document hash → page → block/table row/column/bbox。页面命中不能自动证明 claim 被支持。没有 bbox gold 时，BBox 必须是 N/A。

### 11. Hard negative 如何设计？

candidate 必须来自真实文档，并在 period、entity、metric、basis、currency、segment 或 document source 上与 positive 冲突。不能手写 fake candidate。

### 12. 银行部署时权限过滤放在哪里？

权限应在 retrieval boundary 之前或由可信授权层强制执行。当前 Backend v1 只有 authorizer hook；有 security filter 但没有 authorizer 时返回 403，不能叫 production RBAC/ABAC。

### 13. 为什么 API contract 要与内部 Evidence 解耦？

内部 Evidence 会随实验重构；外部 Agent 需要稳定 versioned contract。EvidenceObject 把 provenance、content、financial、structure、verification 分开，调用方不需要 import parser、retriever 或 CLIP。

### 14. D3 self-coverage=1.0 为什么不可信？

它可能只说明自己定义的 fact list 有 lexical overlap。一个 evidence 可以被复用多个不同 role，所以必须看 Independent CER、Critical Coverage 和 Invalid Reuse Rate。

### 15. Derived fact 为什么不直接检索？

YoY 需要 current value 和 prior value。最终增长率应该由输入 facts 和 calculation receipt 支撑；一段恰好写着增长率的文字不能替代输入、公式、unit 和 period 的验证。

### 16. D1 malformed JSON 算模型失败吗？

报告中是 N/A / MALFORMED_LLM_JSON，因为没有通过 output contract，不能进入 requirement quality comparison。它说明 integration failure，不是合格的 decomposition quality score。

### 17. Structure invariant=1.0 为什么不能写成 accuracy=1.0？

identity 和 row/column relation 是 IR invariants；semantic cell value、unit、merged header、footnote 是否正确需要独立 gold。没有 verified gold 就必须是 N/A。

### 18. 为什么不把所有 retrieval 放进 Agent？

当前 bounded deterministic loop 已足够验证 evidence mechanism。Agent loop 会增加不可控性，但不会自动解决 evidence mapping 和 critical coverage。

### 19. 最大技术瓶颈是什么？

不是单一 embedding。当前最明显的是 evidence mapping/entailment、TableIR semantic correctness、visual grounding、version/conflict handling，以及 requirement decomposition 与底层 capability 的断点。

### 20. 项目最终证明了什么？

证明了一个可复现的 evidence qualification 和 failure-oriented evaluation path，能够把 relevance、completeness、independent coverage、structure fidelity、visual recovery 和 citation provenance 分开测量。没有证明一个普遍优于 text、生产就绪的 multimodal RAG。

## 23. 简历项目描述

以下版本只使用真实实现和正式实验，没有写入未运行的 Milvus、Neo4j、Kubernetes、Qwen-VL 或 neural reranker。

### 中文通用版

**FinEvidence｜面向高风险金融问题的 Evidence-Qualified Retrieval Backend**

- 针对金融 RAG 中“语义相关但证据不充分”的风险，构建 immutable Evidence IR、Requirement Graph、Fact–Evidence Alignment 与 Independent/Critical Coverage，验证 D3 Raw Self Coverage 1.0000 因 invalid evidence reuse 降至 Independent CER 0.7283、Critical Coverage 0.7400。
- 将受控机制迁移到 100-case RealFinance-v1（50 TAT-QA + 50 FinQA），观察 Dense/Hybrid Recall@5 为 0.0900/0.1417、Gold Final CER 为 0.8900，定位 requirement decomposition 和 evidence mapping 为独立瓶颈。
- 在真实 HSBC FY2025 Annual Report/Pillar 3 上运行 CPU CLIP RN50 page-image retrieval、performance-blind benchmark audit 和 NaturalMultimodal control，发现 VisualStress construction bias，并确认自然 page workload 上 Parsed Page Text @10 0.5875 高于 Visual @10 0.0750。
- 基于真实 HSBC PDF pages 1–26 实现 geometry-assisted TableIR，保留 table/row/column/bbox/provenance；24 regions、13 pages 的 identity/row-column invariants 为 1.0000，T2 在 table slice @10 恢复 5/24 页面但 semantic accuracy 保持 N/A。
- 将 retrieval、coverage、verification 和 citation 封装为版本化 Evidence Backend v1，使上层 AI Investment Research Agent 无需依赖 parser、retriever、CLIP 或 benchmark 内部实现。

### AI Agent Engineer 定向版

**FinEvidence｜Evidence Backend for AI Investment Research Agents**

- Designed a versioned EvidenceObject and HTTP API boundary separating Agent planning/generation from retrieval, qualification, citation, and provenance.
- Added requirement-aware search → coverage → verify → citation workflow with ELIGIBLE/PARTIAL/INSUFFICIENT semantics and a fail-closed security-filter boundary.
- Preserved evidence IDs, document hashes, page/table/row/column metadata and optional bbox so Agent claims can be audited without importing internal retriever/parser code.
- Diagnosed why always-on multimodal routing was unsafe: mixed routing achieved recall 1.0000 but unnecessary visual invocation 65.0%; retained conditional escalation as measured but unproven cost optimization.
- Built local contract tests and smoke-verified the API with a 984-item HSBC evidence catalog; full tests passed 81 cases.

### LLM / RAG 算法工程师定向版

**FinEvidence｜Failure-Aware Financial Retrieval and Evidence Qualification**

- Evaluated Dense, Hybrid, facet-aware, visual, fusion and conditional retrieval across controlled fixtures, RealFinance-v1 and real HSBC disclosures with explicit Recall, MRR, nDCG, CER and HN Error metrics.
- Implemented Requirement Graph decomposition with retrieved/derived/explanatory facts, typed dependencies, one-to-one requirement matching and Independent Coverage.
- Demonstrated false completeness: D3 Raw Self Coverage 1.0000 versus Independent CER 0.7283, with Invalid Reuse Rate 0.4100.
- Implemented deterministic TableIR extraction over real HSBC PDF geometry; separated structure invariants from semantic table accuracy and retained unverified fields as N/A.
- Audited multimodal benchmark bias and showed that Natural HSBC page retrieval favored Parsed Page Text @10 0.5875 over CLIP Visual @10 0.0750 on the fixed control set.

### 金融 AI / 银行 AI Engineer 定向版

**FinEvidence｜可审计的金融证据基础设施**

- 面向财报和 Pillar 3 披露，建立 document/page/block/table provenance、SHA-256、citation 和 evidence qualification contract。
- 将“相关内容”与“足以支持金融结论”分开，使用 Critical Requirement Gate 阻止缺关键事实时获得完整回答资格。
- 在 TAT-QA/FinQA public-derived slice 上验证真实检索困难，在 HSBC disclosure 上验证 temporal、metric、entity、basis、table 和 visual/layout failures。
- 通过 benchmark integrity audit 发现 VisualStress 的固定模板和 keyword selection bias，避免把有偏 stress score 当作自然金融能力。
- 提供 search、coverage、table query、verify、citation API，为上层 AI 投研系统提供可追踪、可复核的 evidence foundation。

## 24. 事实、证据和声明强度

本文使用以下标签：

| 标签 | 含义 |
|---|---|
| Observed | 直接来自 metrics、trace、Git output 或实际 smoke |
| Inferred | 基于 failure pattern 的技术判断，不是严格因果证明 |
| Verified | 有固定 manifest、hash、双 run 或测试支持 |
| N/A | 没有可靠 gold、模型未通过 contract 或外部数据未取得 |
| Proposed | 下一阶段可能的设计，不是当前能力 |
| Blocked | 外部资源、权限、网络等条件导致无法完成 |

必须保持的表达：

- HSBCVisualStress-v1 是 project-created stress benchmark，不是 HSBC official benchmark。
- HSBCNaturalMultimodal-v1 是 project-created natural control，不是 public leaderboard。
- RequirementAdjudicated-v1 是 model-assisted adjudicated，不是 human/expert gold。
- T1 Parsed Page Text 不是 verified Structured Table IR。
- T2 Real Structured Table IR 是 deterministic executor，不是 neural reranker。
- CLIP RN50 是 visual retrieval encoder，不是 generative VLM。
- B3 仍是 PARTIAL，因为 FinRAGBench-V public page-image track 未完成。
- B4/B4.1 的 COMPLETE 只在各自 scoped experimental phase 内成立。
- Evidence Backend v1 已实现，但不是 production-scale service。

## 25. 审计来源

项目策略和知识库：

- ../../PROJECT_STRATEGY.md
- ../../BENCHMARK_AND_HARD_CASE_PLAN.md
- ../../CHAT_KNOWLEDGE_BASE.md

阶段报告：

- ../reports/p0-d-real-finance-validation.md
- ../reports/p0-e-evidence-requirement-understanding.md
- ../reports/p0-g-evidence-requirement-graph.md
- ../reports/p0-h-gold-requirement-hsbc-natural-hardcases.md
- ../reports/b3-multimodal-evidence-retrieval.md
- ../reports/b3-1-public-benchmark-evaluation-closure.md
- ../reports/b3-2-benchmark-integrity-public-closure.md
- ../reports/b4-structure-preserving-evidence-ir-failure-aware-escalation.md
- ../reports/b4-1-real-financial-table-recovery.md

后端文档：

- FIN_EVIDENCE_ARCHITECTURE.md
- FIN_EVIDENCE_API_SPEC.md
- AI_RESEARCH_AGENT_INTEGRATION.md
- ARCHITECTURE_DECISION_RECORD.md
- FIN_EVIDENCE_V1_RELEASE.md

关键 Git 实现节点：

    P0-D     d97557d
    P0-E     ea7876b
    P0-G     429058e (implementation) / ce0167f (formal run report)
    P0-H     9588559
    B3       7589c57
    B3.1     52554ea
    B3.2     622381c
    B4       251b7a8
    B4.1     16137e6
    Backend  2990cb2 / 0cd1f7c

## 26. 最后一句话

FinEvidence 没有证明更大的模型、更多 modality 或更复杂 Agent 会自动带来更可靠的金融答案。它证明了一个更基础、也更难被替代的工程原则：

> 在高风险金融系统里，真正的 retrieval 结果不是“我找到了一段相关文本”，而是“我能指出问题需要哪些关键 evidence，并证明每一项都由正确角色、可独立验证、可追踪的 evidence 或合法 derivation 支持；如果做不到，我知道自己没有回答资格”。
