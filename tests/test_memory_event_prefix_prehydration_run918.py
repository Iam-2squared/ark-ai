"""Disposable Memory event-prefix corruption must fail before Python hydration.

All fault rows are synthetic SQLite fixtures. A local prefix is not a writer
identity, independent witness, permission grant or external-action authority.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_event_prefix_review as prefix


@pytest.mark.parametrize(
    "field,payload",
    (
        ("memory_id", "mem_" + "a" * 1_000_000),
        ("owner_id", "x" * 1_025),
        ("namespace", "日" * 342),
        ("owner_id", sqlite3.Binary(b"x" * 50_000)),
        ("namespace", sqlite3.Binary(b"x" * 50_000)),
    ),
)
def test_corrupt_event_rejected_before_cursor_hydrates_private_text(
    tmp_path, field, payload,
):
    store = SQLiteMemoryStore(
        tmp_path / "event-prefix-preflight.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "private")
    store.put(MemoryWrite(scope, "source", "synthetic private content"))
    original = prefix.capture_local_memory_event_prefix(store)
    # Names are static test constants, never untrusted interpolated SQL.
    assert field in ("memory_id", "owner_id", "namespace")
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            f"UPDATE memory_events SET {field}=? WHERE event_id=1",
            (payload,),
        )
    with pytest.raises(
        prefix.MemoryEventPrefixRejected, match="hydration admission",
    ):
        prefix.capture_local_memory_event_prefix(store)
    with pytest.raises(
        prefix.MemoryEventPrefixRejected, match="hydration admission",
    ):
        prefix.compare_local_memory_event_prefix(store, original)


def test_unbounded_retained_digest_rejected_before_read_or_regex(tmp_path, monkeypatch):
    store = SQLiteMemoryStore(
        tmp_path / "witness-preflight.sqlite", clock_ms=lambda: 1000,
    )
    witness = prefix.capture_local_memory_event_prefix(store)
    malformed = replace(witness, prefix_sha256="a" * 1_000_000)

    def forbidden_scan(*_args, **_kwargs):
        pytest.fail("invalid witness must not access SQLite")

    monkeypatch.setattr(prefix, "_scan", forbidden_scan)
    with pytest.raises(prefix.MemoryEventPrefixRejected, match="prefix shape"):
        prefix.compare_local_memory_event_prefix(store, malformed)


def test_small_multibyte_scope_and_retained_prefix_still_work(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "healthy-prefix.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("日本語", "日常")
    store.put(MemoryWrite(scope, "one", "synthetic"))
    retained = prefix.capture_local_memory_event_prefix(store)
    store.put(MemoryWrite(scope, "two", "synthetic"))
    comparison = prefix.compare_local_memory_event_prefix(store, retained)
    assert comparison.previous_event_count == 1
    assert comparison.current_event_count == 2
    assert comparison.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert comparison.action_authorized is False
    assert comparison.memory_disclosure_authorized is False
