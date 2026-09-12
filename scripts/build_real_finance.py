from __future__ import annotations

import argparse
from pathlib import Path

from finevidence.benchmarks.real_finance import build_real_finance_slice


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    workspace_root = root.parent
    parser = argparse.ArgumentParser(description="Build the fixed RealFinance-v1 derived slice.")
    parser.add_argument("--tatqa", default=str(workspace_root / "research/repos/tat-qa/dataset_raw/tatqa_dataset_dev.json"))
    parser.add_argument("--finqa", default=str(workspace_root / "research/repos/FinQA/dataset/dev.json"))
    parser.add_argument("--output", default=str(root / "benchmarks/real_finance_v1"))
    args = parser.parse_args()
    print(build_real_finance_slice(Path(args.tatqa), Path(args.finqa), Path(args.output)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
