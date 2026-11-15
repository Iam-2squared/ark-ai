"""Separate-interpreter SQLite Memory CAS and append-event continuity.

Only synthetic scopes and a disposable local database. A child process has
no external executor, credentials, user data, or authority to share memory.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore


_CHILD = """
import sys
from pathlib import Path

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore

store = SQLiteMemoryStore(Path(sys.argv[1]), clock_ms=lambda: 200)
scope = MemoryScope("offline-owner", sys.argv[2])
try:
    record = store.put(
        MemoryWrite(scope, "shared-source", sys.argv[4]),
        expected_revision=int(sys.argv[3]),
    )
except MemoryConflictError:
    print("CONFLICT")
else:
    print(f"REVISION={record.revision}")
"""


def _child(path, namespace: str, revision: int, text: str) -> str:
    completed = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path), namespace, str(revision), text],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _store(path, now=100):
    return SQLiteMemoryStore(path, clock_ms=lambda: now)


def test_child_commit_updates_parent_view_and_contiguous_global_events(tmp_path):
    path = tmp_path / "isolated-cas.sqlite"
    parent = _store(path)
    scope = MemoryScope("offline-owner", "notes")
    initial = parent.put(
        MemoryWrite(scope, "shared-source", "first"), expected_revision=0,
    )
    assert _child(path, "notes", 1, "child-second") == "REVISION=2"
    assert parent.get(initial.memory_id, scope).content == "child-second"
    with pytest.raises(MemoryConflictError):
        parent.put(
            MemoryWrite(scope, "shared-source", "parent-stale"),
            expected_revision=1,
        )
    events = _store(path).events(scope)
    assert [(event.event_id, event.operation, event.revision) for event in events] == [
        (1, "create", 1), (2, "update", 2),
    ]


def test_failed_child_cas_consumes_no_event_id_after_restart(tmp_path):
    path = tmp_path / "stale-cas.sqlite"
    scope = MemoryScope("offline-owner", "notes")
    parent = _store(path)
    parent.put(MemoryWrite(scope, "shared-source", "one"), expected_revision=0)
    assert _child(path, "notes", 0, "stale") == "CONFLICT"
    assert [(event.event_id, event.revision) for event in _store(path).events(scope)] == [
        (1, 1),
    ]
    winner = parent.put(
        MemoryWrite(scope, "shared-source", "two"), expected_revision=1,
    )
    assert winner.revision == 2
    assert [event.event_id for event in _store(path).events(scope)] == [1, 2]


def test_child_cas_does_not_modify_same_source_in_different_namespace(tmp_path):
    path = tmp_path / "scope-cas.sqlite"
    parent = _store(path)
    notes = MemoryScope("offline-owner", "notes")
    private = MemoryScope("offline-owner", "private")
    first = parent.put(
        MemoryWrite(notes, "shared-source", "notes"), expected_revision=0,
    )
    second = parent.put(
        MemoryWrite(private, "shared-source", "private"), expected_revision=0,
    )
    assert _child(path, "notes", 1, "notes-updated") == "REVISION=2"
    resumed = _store(path)
    assert resumed.get(first.memory_id, notes).content == "notes-updated"
    assert resumed.get(second.memory_id, private).content == "private"
    assert [event.event_id for event in resumed.events(notes)] == [1, 3]
    assert [event.event_id for event in resumed.events(private)] == [2]
