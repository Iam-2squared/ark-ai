"""Memory multi-scope expiry must retain a globally dense append history.

Disposable SQLite, synthetic scopes and isolated Python process only.
No real personal context access, write permission or Candidate is involved.
"""

import subprocess
import sys

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

_CHILD = """
import sys
from pathlib import Path
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
store = SQLiteMemoryStore(Path(sys.argv[1]), clock_ms=lambda: 200)
record = store.put(
    MemoryWrite(MemoryScope("synthetic-owner", "notes"), "shared", "renewed"),
    expected_revision=1,
)
print(record.revision)
"""


def _store(path, now):
    return SQLiteMemoryStore(path, clock_ms=lambda: now)


def _write(scope, *, expiring=True):
    return MemoryWrite(
        scope, "shared", "initial",
        expires_at_ms=150 if expiring else None,
    )


def test_scoped_expiry_preserves_foreign_namespace_until_global_purge(tmp_path):
    path = tmp_path / "scoped-expiry.sqlite"
    notes = MemoryScope("synthetic-owner", "notes")
    private = MemoryScope("synthetic-owner", "private")
    writer = _store(path, 100)
    first = writer.put(_write(notes), expected_revision=0)
    second = writer.put(_write(private), expected_revision=0)

    at_200 = _store(path, 200)
    assert at_200.purge_expired(scope=notes) == 1
    assert at_200.get(first.memory_id, notes, include_expired=True) is None
    assert at_200.get(second.memory_id, private, include_expired=True) is not None
    assert [(e.event_id, e.operation) for e in at_200.events(notes)] == [
        (1, "create"), (3, "expire"),
    ]
    assert [(e.event_id, e.operation) for e in at_200.events(private)] == [
        (2, "create"),
    ]

    assert _store(path, 200).purge_expired() == 1
    cold = _store(path, 200)
    assert cold.get(second.memory_id, private, include_expired=True) is None
    assert [(e.event_id, e.operation) for e in cold.events(private)] == [
        (2, "create"), (4, "expire"),
    ]
    assert cold.purge_expired() == 0


def test_cross_process_refresh_survives_global_expiry_of_other_scope(tmp_path):
    path = tmp_path / "cross-process-global-expiry.sqlite"
    notes = MemoryScope("synthetic-owner", "notes")
    private = MemoryScope("synthetic-owner", "private")
    store = _store(path, 100)
    live = store.put(_write(notes), expected_revision=0)
    expired = store.put(_write(private), expected_revision=0)
    child = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path)],
        text=True, capture_output=True, check=False, timeout=30,
    )
    assert child.returncode == 0, child.stderr
    assert child.stdout.strip() == "2"
    assert _store(path, 300).purge_expired() == 1

    cold = _store(path, 300)
    assert (cold.get(live.memory_id, notes).content,
            cold.get(live.memory_id, notes).revision) == ("renewed", 2)
    assert cold.get(expired.memory_id, private, include_expired=True) is None
    assert [(e.event_id, e.operation) for e in cold.events(notes)] == [
        (1, "create"), (3, "update"),
    ]
    assert [(e.event_id, e.operation) for e in cold.events(private)] == [
        (2, "create"), (4, "expire"),
    ]
