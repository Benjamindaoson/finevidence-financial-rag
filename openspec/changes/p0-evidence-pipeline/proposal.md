## Why

普通的金融 RAG 可能在检索成功、生成成功的同时返回错误证据：文件级词面检索会命中教材书目信息，表格 flatten 会丢失行列关系，而 Top-K 命中部分证据并不能证明答案所需的证据集合完整。当前项目已经完成失败面研究，下一步必须把这些风险收敛成一个可运行、可比较、可复现的 P0 闭环。

## What Changes

- 新建独立 `finevidence/` 实现目录，不修改研究用候选仓库。
- 定义最小 Evidence IR，使证据可定位到 document、page、block、bbox、table、row、column，并保留 content hash。
- 建立固定的 FinEvidence MiniBench 数据格式和 manifest，优先使用可公开复核的金融材料与人工标注 evidence set。
- 实现四级离线 baseline：B0 Dense、B1 Hybrid + Generic Reranker、B2 Evidence Coverage、B3 Conditional Visual Retrieval。
- 实现 evidence set coverage、unsupported answer、hard-negative ranking、citation 和 numerical 评估接口。
- 每次运行保存 config、代码 commit、dataset manifest、prediction、metrics 和 failure cases；没有真实数据时输出 `N/A`，不填提升数字。
- 暂不实现 GraphRAG、Agent、ACL/ABAC、Kubernetes、完整 API 服务或模型训练。

## Capabilities

### New Capabilities

- `evidence-ir`: 可定位、可哈希、可序列化的文本/表格/图像证据记录。
- `mini-benchmark`: 固定数据清单、问题、答案、required evidence 和 failure type。
- `retrieval-baselines`: B0/B1/B2/B3 可重复运行的离线检索管线。
- `evidence-evaluation`: 检索、证据完整性、hard-negative、引用和数值结果评估。

### Modified Capabilities

无。`finevidence/` 是新建独立实现，不改变候选仓库的既有需求。

## Impact

- 新增 Python 3.12 项目、轻量依赖和 pytest 测试。
- 主要影响目录为 `src/`、`benchmarks/mini_finance/`、`configs/`、`scripts/`、`tests/` 和运行产物目录。
- 首轮允许使用本地可复核 Markdown/HTML/JSON 材料；公开大规模视觉 benchmark 只记录 manifest，不在本变更中盲目下载全量数据。
