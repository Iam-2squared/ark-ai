"""Restarted Memory lifetime reuse cannot redeem an earlier generation token.

Synthetic local SQLite and subprocesses only; no external action or consent.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)

_CHILD = """
from pathlib import Path
import sys
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

path, mode, memory_id = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
scope = MemoryScope("owner-a", "private")
store = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
if mode == "expire":
    assert store.purge_expired(scope=scope) == 1
else:
    assert mode == "delete"
    assert store.delete(memory_id, scope, expected_revision=1)
reborn = store.put(
    MemoryWrite(scope, "source-a", "reborn", expires_at_ms=5000),
)
assert reborn.memory_id == memory_id
assert reborn.revision == 1
"""


@pytest.mark.parametrize("mode", ("expire", "delete"))
def test_cold_process_reuses_identity_but_not_cas_generation(
    tmp_path: Path, mode: str,
) -> None:
    path = tmp_path / "memory.sqlite"
    owner_a = MemoryScope("owner-a", "private")
    owner_b = MemoryScope("owner-b", "private")
    first_store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    original = first_store.put(
        MemoryWrite(owner_a, "source-a", "first", expires_at_ms=1500),
    )
    other = first_store.put(
        MemoryWrite(owner_b, "source-b", "separate", expires_at_ms=8000),
    )
    old_a = observe_memory_generation_for_cas(
        first_store, owner_a, "source-a",
    )
    old_b = observe_memory_generation_for_cas(
        first_store, owner_b, "source-b",
    )
    result = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path), mode, original.memory_id],
        capture_output=True, text=True, timeout=45, check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 2001)
    current = cold.get(original.memory_id, owner_a)
    assert current is not None
    assert current.memory_id == original.memory_id
    assert current.revision == old_a.revision == 1
    assert current.content == "reborn"
    fresh = observe_memory_generation_for_cas(cold, owner_a, "source-a")
    assert fresh.create_event_id > old_a.create_event_id
    assert fresh.last_event_id > old_a.last_event_id
    assert fresh.row_sha256 != old_a.row_sha256
    assert fresh.consent_authenticated is False

    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            cold,
            MemoryWrite(
                owner_a, "source-a", "forbidden-old-token",
                expires_at_ms=4500,
            ),
            retained=old_a,
        )
    assert cold.get(original.memory_id, owner_a) == current
    assert [(event.event_id, event.operation, event.revision)
            for event in cold.events(owner_a)] == [
        (1, "create", 1),
        (3, mode, 1),
        (4, "create", 1),
    ]
    # A lifetime rollover cannot invalidate or authorize another owner.
    assert cold.get(other.memory_id, owner_b) == other
    updated_b = generation_fenced_memory_update(
        cold,
        MemoryWrite(
            owner_b, "source-b", "updated-separate",
            expires_at_ms=8000,
        ),
        retained=old_b,
    )
    assert updated_b.revision == 2
    assert updated_b.content == "updated-separate"
    assert [(event.event_id, event.operation, event.revision)
            for event in cold.events(owner_b)] == [
        (2, "create", 1), (5, "update", 2),
    ]
