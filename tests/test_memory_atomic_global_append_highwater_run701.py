"""Global append integrity for same-transaction Memory epoch diagnostics.

All files are disposable SQLite fixtures. Global high-water is local evidence,
not an authenticated author, trusted clock, consent or authorization to write.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory.atomic_epoch_review import review_atomic_memory_epoch
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "atomic-global-append.sqlite", clock_ms=lambda: 1000,
    )
    own = MemoryScope("owner", "notes")
    foreign = MemoryScope("other", "private")
    return store, own, foreign


def _append(store, scope, source):
    store.put(MemoryWrite(scope, source, "synthetic private payload"))


@pytest.mark.parametrize("missing_event", (1, 2, 3))
def test_foreign_first_middle_last_event_loss_denied_for_empty_scope(
    tmp_path, missing_event,
):
    store, own, foreign = _case(tmp_path)
    for n in range(3):
        _append(store, foreign, f"other-{n}")
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=?", (missing_event,))
    with pytest.raises(MemorySchemaError, match="global event high-water"):
        review_atomic_memory_epoch(store, (own,))


def test_other_scope_append_loss_denied_even_when_own_history_is_coherent(tmp_path):
    store, own, foreign = _case(tmp_path)
    _append(store, own, "own-1")
    _append(store, foreign, "foreign-1")
    _append(store, own, "own-2")
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=2")
    with pytest.raises(MemorySchemaError, match="global event high-water"):
        review_atomic_memory_epoch(store, (own,))


def test_forged_global_autoincrement_tail_denied(tmp_path):
    store, own, foreign = _case(tmp_path)
    _append(store, foreign, "foreign")
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE sqlite_sequence SET seq=9 WHERE name='memory_events'"
        )
    with pytest.raises(MemorySchemaError, match="global event high-water"):
        review_atomic_memory_epoch(store, (own,))


def test_intact_unrelated_history_does_not_disclose_or_grant(tmp_path):
    store, own, foreign = _case(tmp_path)
    _append(store, foreign, "foreign")
    report = review_atomic_memory_epoch(store, (own,))
    assert report.row_counts == (0,)
    assert report.event_counts == (0,)
    assert report.event_tail_ids == (0,)
    assert report.independent_writer_proven is False
    assert report.memory_disclosure_authorized is False
    assert report.dispatch_authorized is False
    assert "synthetic private payload" not in repr(report)


def test_foreign_append_during_clock_callback_does_not_mix_wal_epochs(tmp_path):
    store, own, foreign = _case(tmp_path)
    peer = SQLiteMemoryStore(store.path, clock_ms=lambda: 1001)
    _append(store, own, "first")
    calls = []

    def interleaved_clock():
        calls.append(True)
        _append(peer, foreign, "foreign-after-snapshot")
        return 1000

    store._clock_ms = interleaved_clock
    before = review_atomic_memory_epoch(store, (own,))
    assert calls == [True]
    assert before.row_counts == (1,)
    assert before.event_counts == (1,)

    store._clock_ms = lambda: 1002
    after = review_atomic_memory_epoch(store, (own,))
    assert after.row_counts == (1,)
    assert after.event_counts == (1,)
    assert after == before or after.epoch_digest != before.epoch_digest
    assert after.dispatch_authorized is False
