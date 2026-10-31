"""Retention receipt must track exact validated row bytes, not only status."""

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import (
    RetentionState,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _case(tmp_path: Path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "private")
    memory.put(MemoryWrite(
        scope, "source", "private-before", metadata={"tag": "first"},
        expires_at_ms=150,
    ))
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    return memory, scope, ledger


def _review(case):
    memory, scope, ledger = case
    return review_synthetic_retention_inventory(
        memory, scope, ledger, now_ms=100,
    )


@pytest.mark.parametrize(
    "change",
    ["content", "metadata", "expiry", "created"],
)
def test_receipt_detects_coherent_row_drift_without_revision_or_state_change(
    tmp_path: Path, change: str,
):
    case = _case(tmp_path)
    first = _review(case)
    assert len(first.items) == 1
    assert first.items[0].state is RetentionState.NOT_EXPIRED
    with sqlite3.connect(case[0].path) as conn:
        if change == "content":
            content = "private-after"
            conn.execute(
                "UPDATE memories SET content=?,content_sha256=?",
                (content, hashlib.sha256(content.encode()).hexdigest()),
            )
        elif change == "metadata":
            metadata = json.dumps(
                {"tag": "second"}, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            )
            conn.execute(
                "UPDATE memories SET metadata_json=?", (metadata,),
            )
        elif change == "expiry":
            conn.execute(
                "UPDATE memories SET expires_at_ms=151",
            )
        else:
            conn.execute(
                "UPDATE memories SET created_at_ms=99",
            )
    second = _review(case)
    assert first.items == second.items
    assert first.scope_digest == second.scope_digest
    assert first.reviewed_at_ms == second.reviewed_at_ms
    assert first.revoked == second.revoked is False
    assert first.inventory_digest != second.inventory_digest
    assert second.context_use_authorized is False
    assert second.deletion_authorized is False
    assert second.erasure_completed is False
    assert "private-before" not in repr(second)
    assert "private-after" not in repr(second)
    assert "first" not in second.inventory_digest
    assert "second" not in second.inventory_digest


def test_unchanged_memory_receipt_is_deterministic(tmp_path: Path):
    case = _case(tmp_path)
    first = _review(case)
    second = _review(case)
    assert first == second
    assert first.inventory_digest.startswith("retention_")
