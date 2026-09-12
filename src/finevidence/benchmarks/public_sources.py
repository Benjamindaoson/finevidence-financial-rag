from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


def _commit(repo: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "N/A"


def audit_public_sources(sources: dict) -> dict:
    result = {}
    for name, spec in sources.items():
        repo = Path(spec["repo"]).resolve()
        files = []
        missing = []
        for raw_path in spec.get("files", []):
            path = repo / raw_path
            item = {"relative_path": str(raw_path), "exists": path.exists()}
            if not path.exists():
                missing.append(str(raw_path))
            else:
                data = path.read_bytes()
                item.update({"byte_size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
                try:
                    decoded = json.loads(data.decode("utf-8"))
                    item["record_count"] = len(decoded) if isinstance(decoded, list) else None
                except (UnicodeDecodeError, json.JSONDecodeError):
                    item["record_count"] = None
            files.append(item)
        result[name] = {
            "status": "READY" if not missing else "BLOCKED",
            "repo": str(repo),
            "repo_url": spec.get("repo_url", "N/A"),
            "commit": _commit(repo),
            "license_note": spec.get("license_note", "N/A"),
            "files": files,
            "missing_files": missing,
        }
    return result
