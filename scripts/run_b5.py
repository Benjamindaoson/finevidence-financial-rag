from __future__ import annotations

import argparse
import json
from pathlib import Path

from finevidence.eval.b5 import run_b5_1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded B5 retrieval experiments.")
    parser.add_argument("--stage", choices=("b5.1",), default="b5.1")
    parser.add_argument("--config", default="configs/b5_1_cpu.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    run = run_b5_1(json.loads(config_path.read_text(encoding="utf-8")))
    print(run.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
