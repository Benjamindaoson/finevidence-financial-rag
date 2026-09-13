# B5 Cost and Latency

## B5.1 CPU reference run

Source: latest fresh run under `artifacts/b5_1_runs/`.

| Component | P50 ms | P95 ms |
|---|---:|---:|
| Current dense index | 1393.67 | 1393.67 |
| Current hybrid index | 2830.04 | 2830.04 |
| Qwen index | N/A | N/A |
| Current dense query | 13.29 | 15.87 |
| Current hybrid query | 58.78 | 105.69 |
| Qwen query | N/A | N/A |

These are CPU timings for the local reference implementation. No GPU or
monetary cost is claimed. The uncompleted Qwen download is not mixed into
query latency.

## Cost boundary

Until an actual neural checkpoint executes, GPU seconds, neural index size,
and model inference cost are `N/A`. The controller contract already carries
latency and cost fields so later bounded experiments can measure them without
changing the Evidence contract.
