"""Retention inventory rejects malformed private SQLite cells before SELECT *.

Synthetic files only. Read-only diagnostics never establish erasure, consent,
disclosure permission, external effect, or trusted wall-clock provenance.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.personal_context_retention_review import (
    RetentionState,
    SyntheticRetentionRejected,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _fixture(tmp_path):
    memory = SQLiteMemoryStore(
        tmp_path / "synthetic-memory.sqlite", clock_ms=lambda: 100,
    )
    scope = MemoryScope("private-synthetic-owner", "notes")
    record = memory.put(MemoryWrite(
        scope, "fixture", "SYNTHETIC-PRIVATE-CONTENT", expires_at_ms=150,
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "synthetic-veto.sqlite")
    return memory, scope, record, veto


@pytest.mark.parametrize(
    "field,payload",
    (
        ("content", "x" * 4_000_001),
        ("source_id", "x" * 2_049),
        ("memory_id", "mem_" + "a" * 1_000_000),
        ("content_sha256", "a" * 1_000_000),
        ("metadata_json", sqlite3.Binary(b"{}")),
    ),
)
def test_retention_rejects_corrupt_sqlite_cells_before_private_row_hydration(
    tmp_path, field, payload,
):
    memory, scope, record, veto = _fixture(tmp_path)
    assert field in (
        "content", "source_id", "memory_id", "content_sha256", "metadata_json",
    )
    with sqlite3.connect(memory.path) as conn:
        conn.execute(
            f"UPDATE memories SET {field}=? WHERE memory_id=?",
            (payload, record.memory_id),
        )
    with pytest.raises(SyntheticRetentionRejected, match="hydration admission") as exc:
        review_synthetic_retention_inventory(
            memory, scope, veto, now_ms=100,
        )
    message = str(exc.value)
    assert "SYNTHETIC-PRIVATE-CONTENT" not in message
    assert "private-synthetic-owner" not in message


def test_valid_private_rows_still_classify_at_inclusive_expiry_boundary(tmp_path):
    memory, scope, expiring, veto = _fixture(tmp_path)
    future = memory.put(MemoryWrite(
        scope, "future", "SYNTHETIC FUTURE", expires_at_ms=200,
    ))
    forever = memory.put(MemoryWrite(
        scope, "unbounded", "SYNTHETIC NO EXPIRY",
    ))
    result = review_synthetic_retention_inventory(
        memory, scope, veto, now_ms=150,
    )
    states = {item.memory_id: item.state for item in result.items}
    assert states[expiring.memory_id] is RetentionState.EXPIRED
    assert states[future.memory_id] is RetentionState.NOT_EXPIRED
    assert states[forever.memory_id] is RetentionState.NO_EXPIRY
    assert result.expired_count == 1
    assert result.context_use_authorized is False
    assert result.deletion_authorized is False
    assert result.erasure_completed is False
    assert "SYNTHETIC-PRIVATE-CONTENT" not in repr(result)
