from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from apex_fresh.config import get_config


def marker_path(name: str) -> Path:
    cfg = get_config()
    return Path(cfg.completion_dir) / f"{name}.md"


def write_marker(name: str, title: str) -> None:
    path = marker_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    path.write_text(f"# {title}\n\nCompleted: {timestamp}\n", encoding="utf-8")


def ensure_marker(name: str) -> None:
    path = marker_path(name)
    if not path.exists():
        raise RuntimeError(f"Required completion marker missing: {path}")

