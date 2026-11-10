"""Independent-owner, independent-process Memory CAS remains isolated.

Only disposable local SQLite and mock clocks are used; tokens are not consent
or authenticated writer receipts. Separate owners must not block each other.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)

_CHILD = """
import json
import sys
from pathlib import Path
from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASToken, MemoryGenerationCASRejected,
    generation_fenced_memory_update,
)
db, owner, token_json, value = sys.argv[1:]
store = SQLiteMemoryStore(Path(db), clock_ms=lambda: 101)
try:
    generation_fenced_memory_update(
        store, MemoryWrite(MemoryScope(owner, "private"), "source", value),
        retained=MemoryGenerationCASToken(*json.loads(token_json)),
    )
except (MemoryConflictError, MemoryGenerationCASRejected):
    sys.exit(4)
"""


def _serialized(token: object) -> str:
    return json.dumps((
        token.memory_id, token.create_event_id, token.last_event_id,
        token.revision, token.event_prefix_sha256, token.row_sha256,
    ))


def test_independent_owners_can_both_commit_across_os_processes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "independent-cas.sqlite"
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scopes = (
        MemoryScope("owner-A", "private"), MemoryScope("owner-B", "private"),
    )
    rows = tuple(initial.put(MemoryWrite(scope, "source", "before"))
                 for scope in scopes)
    tokens = tuple(observe_memory_generation_for_cas(
        initial, scope, "source",
    ) for scope in scopes)
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _CHILD, str(path), scope.owner_id,
             _serialized(token), "after-" + scope.owner_id],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for scope, token in zip(scopes, tokens, strict=True)
    ]
    outputs = [p.communicate(timeout=30) for p in processes]
    assert [p.returncode for p in processes] == [0, 0], outputs
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 102)
    assert sorted(
        event.event_id for scope in scopes for event in cold.events(scope)
    ) == [1, 2, 3, 4]
    for scope, row, old in zip(scopes, rows, tokens, strict=True):
        current = cold.get(row.memory_id, scope)
        assert current is not None
        assert current.revision == 2
        assert current.content == "after-" + scope.owner_id
        fresh = observe_memory_generation_for_cas(cold, scope, "source")
        assert fresh.create_event_id == old.create_event_id
        assert fresh.last_event_id > old.last_event_id
        with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
            generation_fenced_memory_update(
                cold, MemoryWrite(scope, "source", "stale"),
                retained=old,
            )
    assert all(cold.get(row.memory_id, other) is None
               for row, other in zip(rows, reversed(scopes), strict=True))


def test_swapped_owner_generation_cannot_advance_other_scope(
    tmp_path: Path,
) -> None:
    path = tmp_path / "owner-swap.sqlite"
    scope_a, scope_b = MemoryScope("owner-A", "private"), MemoryScope(
        "owner-B", "private",
    )
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    store.put(MemoryWrite(scope_a, "source", "A"))
    store.put(MemoryWrite(scope_b, "source", "B"))
    retained_a = observe_memory_generation_for_cas(store, scope_a, "source")
    before = [tuple((event.event_id, event.operation, event.revision)
                    for event in store.events(scope))
              for scope in (scope_a, scope_b)]
    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            store, MemoryWrite(scope_b, "source", "forged"),
            retained=retained_a,
        )
    after = [tuple((event.event_id, event.operation, event.revision)
                   for event in store.events(scope))
             for scope in (scope_a, scope_b)]
    assert after == before
    assert store.get(retained_a.memory_id, scope_b) is None
