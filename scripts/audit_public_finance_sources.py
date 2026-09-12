from __future__ import annotations

import json
from pathlib import Path

from finevidence.benchmarks.public_sources import audit_public_sources


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    workspace_root = project_root.parent
    sources = {
        "TAT-QA": {
            "repo": workspace_root / "research/repos/tat-qa",
            "repo_url": "https://github.com/NExTplusplus/tat-qa",
            "files": ["dataset_raw/tatqa_dataset_dev.json", "dataset_raw/tatqa_dataset_test_gold.json"],
            "license_note": "Dataset README states CC BY 4.0; verify terms before redistribution.",
        },
        "FinQA": {
            "repo": workspace_root / "research/repos/FinQA",
            "repo_url": "https://github.com/czyssrs/FinQA",
            "files": ["dataset/dev.json", "dataset/test.json"],
            "license_note": "Repository license and dataset terms must be reviewed before redistribution.",
        },
    }
    result = audit_public_sources(sources)
    output = project_root / "data/source_manifests/public_finance_sources.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0 if all(item["status"] == "READY" for item in result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
