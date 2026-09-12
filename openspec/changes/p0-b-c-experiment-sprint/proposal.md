## Why

当前 B2 的 `Complete Evidence Rate` 与 Recall 完全同步，无法证明系统识别了“命中部分证据但事实集合不完整”的问题；当前 B1 的 Hard-Negative Error Rate 为 0.70，说明通用 reranker 没有解决金融指标、年份和实体混淆。下一阶段需要围绕两个可证伪结论推进，而不是继续堆叠功能。

## What Changes

- 冻结现有 `MiniBench-v1`，不修改其数据和 manifest。
- 新增 `EvidenceCompleteness-v1`，将 multi-evidence 标注升级为 `required_facts` 与 `acceptable_evidence_ids`。
- 实现 fact coverage matrix 和 Initial/Final Complete Evidence、Partial→Complete Recovery、False Answer Eligibility 指标。
- 实现由 missing fact 生成 targeted query 的确定性 re-retrieval，最多两轮，并保存每轮 trace。
- 新增 `FinanceHardSet-v1`，包含 100 个按 temporal、metric、entity、segment、basis、geography、currency、period 和 table-context 分层的 hard-negative query。
- 实现 financial facet extraction、facet-aware reranking 和基于 hard-negative pair 的确定性 ranking adapter。
- 用相同 Recall@5、MRR、nDCG@10、HN Error 比较 Dense、Hybrid+Generic、Facet-aware、Hard-negative-aware 四条 ranking pipeline。
- 暂不进入 PDF/page-preserving ingestion、B3 visual retrieval、GraphRAG、Agent、ACL、FastAPI 或 K8s。

## Capabilities

### New Capabilities

- `fact-coverage`: required fact、acceptable evidence、coverage matrix 和 eligibility 指标。
- `targeted-reretrieval`: 基于 missing fact 的有限轮次检索及 per-round trace。
- `financial-ranking`: 金融 facet extraction、facet-aware 与 hard-negative-aware ranking。
- `experiment-suites`: EvidenceCompleteness-v1、FinanceHardSet-v1 和两张可复现结果表。

### Modified Capabilities

无。现有 MiniBench-v1 作为冻结回归输入，不修改其需求或数据。

## Impact

- 修改 `src/finevidence/contracts/benchmark.py` 和 `src/finevidence/evidence/` 的评估契约，同时保持旧字符串 fact 格式兼容。
- 新增 `src/finevidence/ranking/`、targeted retrieval 适配器、两个 benchmark 数据目录和实验 runner。
- 仅使用当前项目已有的 Python、Pydantic、NumPy、scikit-learn、pytest 依赖；不引入外部 LLM/VLM 或训练服务。
- 所有实验继续写入独立 run 目录并记录 commit、manifest、per-query trace 和失败案例。
