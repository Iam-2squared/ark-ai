"""Disconnected occurrence frontier must not read state under changed codecs.

Every case uses a deliberately missing local database and exercises only the
no-execution contract guard. No external effect or clock trust is claimed.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.agency import disconnected_occurrence_frontier_review as frontier
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)


@pytest.mark.parametrize(
    "changed",
    (
        "_DOMAIN",
        "_SHA",
        "hashlib",
        "json",
        "sqlite3",
        "SyntheticOccurrenceStore",
    ),
)
def test_detached_frontier_rejects_protocol_rebinding_before_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed: str,
) -> None:
    store = object.__new__(SyntheticOccurrenceStore)
    missing = tmp_path / "never-created.db"
    store._path = missing
    replacements: dict[str, object] = {
        "_DOMAIN": frontier._DOMAIN + b"altered",
        "_SHA": re.compile(r"[0-9a-f]{64}\\Z"),
        "hashlib": SimpleNamespace(sha256=hashlib.sha256),
        "json": SimpleNamespace(dumps=json.dumps),
        "sqlite3": SimpleNamespace(connect=sqlite3.connect),
        "SyntheticOccurrenceStore": object,
    }
    monkeypatch.setattr(frontier, changed, replacements[changed])
    with pytest.raises(SyntheticReplayRejected, match="contract changed"):
        frontier.review_synthetic_occurrence_frontier(store)
    assert not missing.exists()
