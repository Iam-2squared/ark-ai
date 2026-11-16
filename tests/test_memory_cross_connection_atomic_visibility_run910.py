"""Actual SQLite read isolation while a row and its event are uncommitted.

Synthetic temporary Memory only; no cross-process safety, external deletion,
trusted time, durable backup erasure or real consent is established.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("operation", ("create", "update", "delete", "expire"))
def test_independent_reader_never_sees_half_committed_row_event_pair(
    tmp_path, monkeypatch, operation,
):
    path = tmp_path / "atomic_visibility.sqlite"
    scope = MemoryScope("synthetic-owner", "isolated")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    initial = None
    if operation != "create":
        initial = writer.put(MemoryWrite(
            scope, "original", "old",
            expires_at_ms=150 if operation == "expire" else None,
        ))
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    old_events = tuple(reader.events(scope))
    old_record = (
        None if initial is None else
        reader.get(initial.memory_id, scope, include_expired=True)
    )
    seen = []
    real_event = SQLiteMemoryStore._event

    def inspect_uncommitted(conn, memory_id, event_scope, kind, revision, timestamp):
        real_event(conn, memory_id, event_scope, kind, revision, timestamp)
        assert kind == operation
        # This observer has a separate connection and may not see either the
        # mutation or its matching event until the writer commits both.
        assert tuple(reader.events(scope)) == old_events
        observed = reader.get(memory_id, scope, include_expired=True)
        assert observed == old_record
        seen.append(kind)

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_event", staticmethod(inspect_uncommitted))
        if operation == "create":
            changed = writer.put(MemoryWrite(scope, "new", "new"))
            target = changed.memory_id
        elif operation == "update":
            assert initial is not None
            changed = writer.put(
                MemoryWrite(scope, "original", "new"),
                expected_revision=initial.revision,
            )
            target = initial.memory_id
        elif operation == "delete":
            assert initial is not None
            assert writer.delete(
                initial.memory_id, scope, expected_revision=initial.revision,
            )
            target = initial.memory_id
        else:
            assert initial is not None
            later = SQLiteMemoryStore(path, clock_ms=lambda: 200)
            assert later.purge_expired(scope=scope, limit=1) == 1
            target = initial.memory_id

    assert seen == [operation]
    after = tuple(reader.events(scope))
    assert len(after) == len(old_events) + 1
    assert after[:-1] == old_events
    assert after[-1].operation == operation
    final_record = reader.get(target, scope, include_expired=True)
    if operation in ("delete", "expire"):
        assert final_record is None
    else:
        assert final_record is not None
        assert final_record.content == "new"
