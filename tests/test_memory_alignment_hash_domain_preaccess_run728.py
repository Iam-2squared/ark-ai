"""Local Memory alignment refuses changed hash modules or digest domain.

This uses temporary synthetic SQLite. No memory disclosure, erasure or action.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_event_alignment as alignment


def _store(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 5000)
    store.put(MemoryWrite(
        MemoryScope("owner"), "fixture", "private memory payload",
        metadata={"secret": "not accessible to altered audit dependencies"},
    ))
    return store


@pytest.mark.parametrize("target", (
    "hashlib_module", "json_module", "same_domain_bytes",
))
def test_rebound_memory_audit_dependencies_refused_before_private_sqlite(
    tmp_path, monkeypatch, target,
):
    store = _store(tmp_path)
    if target == "hashlib_module":
        monkeypatch.setattr(alignment, "hashlib", object())
    elif target == "json_module":
        monkeypatch.setattr(alignment, "json", object())
    else:
        monkeypatch.setattr(
            alignment, "_DOMAIN", bytes(bytearray(alignment._DOMAIN)),
        )

    def forbidden_read():
        pytest.fail("changed Memory audit authority reached private SQLite")

    monkeypatch.setattr(store, "_connect_readonly", forbidden_read)
    with pytest.raises(
        alignment.MemoryEventAlignmentRejected, match="digest authority changed",
    ):
        alignment.review_memory_event_alignment(store)


def test_unmodified_memory_alignment_stays_read_only_and_non_authorizing(tmp_path):
    store = _store(tmp_path)
    receipt = alignment.review_memory_event_alignment(store)
    assert receipt.row_count == 1
    assert receipt.event_count == 1
    assert receipt.action_authorized is False
    assert receipt.user_consent_verified is False
    assert receipt.independently_authenticated is False
    assert "private memory payload" not in repr(receipt)
