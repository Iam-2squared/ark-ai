"""Competing OS processes cannot both consume one retained Memory CAS epoch.

The local revision/event journal is authoritative for this disposable SQLite
fixture, not for authenticated writer identity, consent or external effects.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("same_payload", (False, True))
def test_independent_processes_race_one_generation_token(
    tmp_path: Path, same_payload: bool,
) -> None:
    path = tmp_path / "memory-race.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = initial.put(MemoryWrite(scope, "source", "before"))
    token = observe_memory_generation_for_cas(initial, scope, "source")
    persisted = json.dumps((
        token.memory_id, token.create_event_id, token.last_event_id,
        token.revision, token.event_prefix_sha256, token.row_sha256,
    ))
    child = """
import json
import sys
import time
from pathlib import Path
from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASToken, MemoryGenerationCASRejected,
    generation_fenced_memory_update,
)
store = SQLiteMemoryStore(Path(sys.argv[1]), clock_ms=lambda: 101)
retained = MemoryGenerationCASToken(*json.loads(sys.argv[2]))
Path(sys.argv[4]).touch()
gate = Path(sys.argv[5])
deadline = time.monotonic() + 25
while not gate.exists():
    if time.monotonic() >= deadline:
        sys.exit("CAS gate timed out")
    time.sleep(0.02)
try:
    generation_fenced_memory_update(
        store,
        MemoryWrite(MemoryScope("synthetic-owner", "private"), "source", sys.argv[3]),
        retained=retained,
    )
except (MemoryConflictError, MemoryGenerationCASRejected):
    sys.exit(4)
"""
    values = ("after", "after" if same_payload else "different")
    gate = tmp_path / "cas-gate"
    processes: list[subprocess.Popen[str]] = []
    # Keep a local WAL connection alive while the children race. Otherwise a
    # last-connection WAL unlink can race an unrelated path-custody lstat.
    # Start children one by one, so this test measures generation CAS rather
    # than competing SQLite store bootstraps.
    with closing(sqlite3.connect(path)) as wal_keeper:
        assert wal_keeper.execute("PRAGMA journal_mode").fetchone() == ("wal",)
        try:
            for index, value in enumerate(values):
                ready = tmp_path / f"cas-ready-{index}"
                process = subprocess.Popen(
                    [
                        sys.executable, "-c", child, str(path), persisted,
                        value, str(ready), str(gate),
                    ],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )
                processes.append(process)
                deadline = time.monotonic() + 25
                while not ready.exists():
                    if process.poll() is not None:
                        output = process.communicate()
                        raise AssertionError(
                            f"child {index} exited before CAS gate: {output}"
                        )
                    if time.monotonic() >= deadline:
                        raise AssertionError(
                            f"child {index} never reached the CAS gate"
                        )
                    time.sleep(0.02)
            gate.touch()
            outputs = [process.communicate(timeout=35) for process in processes]
        finally:
            gate.touch()
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
    assert sorted(process.returncode for process in processes) == [0, 4], outputs

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 102)
    updated = cold.get(row.memory_id, scope)
    assert updated is not None
    assert updated.revision == 2
    assert updated.content in values
    assert [(event.event_id, event.operation, event.revision)
            for event in cold.events(scope)] == [
        (1, "create", 1), (2, "update", 2),
    ]
    fresh = observe_memory_generation_for_cas(cold, scope, "source")
    assert fresh.create_event_id == token.create_event_id
    assert fresh.last_event_id > token.last_event_id
    assert fresh.event_prefix_sha256 != token.event_prefix_sha256
    assert fresh.external_action_authorized is False
    assert fresh.consent_authenticated is False

    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            cold, MemoryWrite(scope, "source", "old-token-replay"),
            retained=token,
        )
    after_reject = cold.get(row.memory_id, scope)
    assert after_reject == updated
    assert tuple(cold.events(scope))[-1].event_id == 2
