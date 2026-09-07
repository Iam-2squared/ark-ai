import json
from pathlib import Path

from ark.logging import SessionLogger


def test_jsonl_logging(tmp_path: Path) -> None:
    logger = SessionLogger(tmp_path)
    logger.write(role="user", content="こんにちは", model="test")
    event = json.loads(logger.path.read_text(encoding="utf-8"))
    assert event["content"] == "こんにちは"
    assert event["role"] == "user"
