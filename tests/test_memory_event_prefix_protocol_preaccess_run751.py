"""Run751: event prefix grammar/domain rebinding must fail before local reads.

Disposable SQLite only. A local SHA or prefix never authenticates its writer,
permission to disclose Memory, or authority to execute an action.
"""

import re

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_event_prefix_review as prefix


def _store(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "event-protocol-751.sqlite", clock_ms=lambda: 1000,
    )
    store.put(
        MemoryWrite(
            MemoryScope("owner", "private"), "source", "fixture private text",
        ),
    )
    return store


@pytest.mark.parametrize(
    ("name", "replacement"),
    [
        ("_ID", re.compile(r"mem_.*\\Z")),
        ("_SHA", re.compile(r".*\\Z")),
        ("_OPERATIONS", frozenset(("create", "update", "delete", "expire", "promote"))),
        ("_MAX_EVENTS", 40_001),
        ("_DOMAIN", b"ARK-forged-local-event-domain\\0"),
        ("_COMPARISON_DOMAIN", b"ARK-forged-comparison-domain\\0"),
    ],
)
@pytest.mark.parametrize("mode", ("capture", "compare"))
def test_preinstalled_protocol_rebinding_fails_before_sqlite(
    tmp_path, monkeypatch, name, replacement, mode,
):
    store = _store(tmp_path)
    retained = prefix.capture_local_memory_event_prefix(store)
    reads = []

    def forbidden_read(_self):
        reads.append("sqlite")
        raise AssertionError("private event history opened after protocol rebinding")

    with monkeypatch.context() as patch:
        patch.setattr(prefix, name, replacement)
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden_read)
        with pytest.raises(
            prefix.MemoryEventPrefixRejected,
            match="local event prefix protocol changed",
        ):
            if mode == "capture":
                prefix.capture_local_memory_event_prefix(store)
            else:
                prefix.compare_local_memory_event_prefix(store, retained)
    assert reads == []


def test_reentrant_prefix_hash_must_not_change_protocol_midscan(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    original_charge = prefix._charge

    def rebind_after_first_row(hasher, event):
        original_charge(hasher, event)
        monkeypatch.setattr(
            prefix,
            "_OPERATIONS",
            frozenset(("create", "update", "delete", "expire", "promote")),
        )

    monkeypatch.setattr(prefix, "_charge", rebind_after_first_row)
    with pytest.raises(
        prefix.MemoryEventPrefixRejected,
        match="local event prefix protocol changed",
    ):
        prefix.capture_local_memory_event_prefix(store)


def test_unchanged_protocol_preserves_deny_only_append_review(tmp_path):
    store = _store(tmp_path)
    retained = prefix.capture_local_memory_event_prefix(store)
    store.put(
        MemoryWrite(
            MemoryScope("other", "private"), "source", "other fixture text",
        ),
    )
    result = prefix.compare_local_memory_event_prefix(store, retained)
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.previous_event_count == 1
    assert result.current_event_count == 2
    assert result.independent_witness_custody_proven is False
    assert result.historical_writer_authenticated is False
    assert result.memory_disclosure_authorized is False
    assert result.action_authorized is False
