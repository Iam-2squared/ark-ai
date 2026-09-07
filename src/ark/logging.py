"""Structured local session logging."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


class SessionLogger:
    def __init__(self, directory: str | Path = "logs") -> None:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
        self.path = root / f"session_{stamp}.jsonl"

    def write(self, *, role: str, content: str, model: str) -> None:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "role": role,
            "content": content,
            "model": model,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
