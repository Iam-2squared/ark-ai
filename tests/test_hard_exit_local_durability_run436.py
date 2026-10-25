"""Hard process-exit boundaries for disconnected durable SQLite fixtures.

The children use os._exit on disposable local databases to test a real process
termination, not just a Python exception. No ToolBackend, notifications,
real private data, credentials, external compute or human authorization occur.
"""

import sqlite3
import subprocess
import sys

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.sqlite_store import deterministic_memory_id
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)

_MEMORY_CHILD = r"""
import os
import pathlib
import sys

import ark.memory.sqlite_store as memory_module
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

path, phase = pathlib.Path(sys.argv[1]), sys.argv[2]
store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
if phase == "before_event":
    def stop_before_audit(*_args):
        os._exit(41)
    store._event = stop_before_audit
elif phase == "after_commit":
    def stop_after_commit(*_args, **_kwargs):
        os._exit(42)
    memory_module.MemoryRecord = stop_after_commit
else:
    sys.exit("unexpected phase")
store.put(MemoryWrite(MemoryScope("fixture-owner", "notes"),
                      "fixture-source", "synthetic text"))
sys.exit("memory child unexpectedly returned")
"""

_OCCURRENCE_CHILD = r"""
import os
import pathlib
import sys

import ark.agency.durable_occurrence_review as occurrence
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry

class NoDispatch:
    def execute(self, _call):
        raise AssertionError("backend must never execute")

call = ToolCall("inert", "fixture.write", "disconnected", {"test": 1})
registry = ToolRegistry((ToolRegistration(
    "inert", "fixture.write", Effect.WRITE, "mock", NoDispatch(),
),))
token = OneShotAuthorization("hard-exit-fixture-token", call.request_id, 1000)
store = occurrence.SyntheticOccurrenceStore(pathlib.Path(sys.argv[1]))
occurrence.SyntheticReservationReceipt = lambda *_args: os._exit(43)
store.reserve_synthetic(
    registry, call, token, occurrence_id="occ_" + "a" * 64, now_ms=10,
)
sys.exit("occurrence child unexpectedly returned")
"""

_PROACTIVE_CHILD = r"""
import os
import pathlib
import sys

import ark.proactive_synthetic_review as proactive

policy = proactive.SyntheticTriggerPolicy(
    "fixture-owner", "notes", "fixture-event", 1, "fixture-v1", 100, 1000, 1,
)
ledger = proactive.SyntheticProactiveLedger(pathlib.Path(sys.argv[1]))
proactive.SyntheticTriggerReceipt = lambda *_args: os._exit(44)
ledger.prepare(
    policy, source_digest="a" * 64, observation_digest="b" * 64,
    observed_at_ms=1000, now_ms=1001,
)
sys.exit("proactive child unexpectedly returned")
"""


def _hard_exit(script, path, *args, expected):
    completed = subprocess.run(
        [sys.executable, "-c", script, str(path), *args],
        capture_output=True, text=True, timeout=35, check=False,
    )
    assert completed.returncode == expected, (
        completed.returncode, completed.stdout, completed.stderr,
    )


@pytest.mark.parametrize(
    ("phase", "exit_code", "count"),
    [("before_event", 41, 0), ("after_commit", 42, 1)],
)
def test_memory_hard_exit_preserves_row_event_atomicity_and_cas(
    tmp_path, phase, exit_code, count,
):
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "notes")
    write = MemoryWrite(scope, "fixture-source", "synthetic text")
    _hard_exit(_MEMORY_CHILD, path, phase, expected=exit_code)

    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT memory_id, revision, content FROM memories"
        ).fetchall()
        events = conn.execute(
            "SELECT operation, revision FROM memory_events ORDER BY event_id"
        ).fetchall()
    assert len(rows) == count
    assert len(events) == count
    if count:
        assert rows == [(deterministic_memory_id(scope, "fixture-source"),
                         1, "synthetic text")]
        assert events == [("create", 1)]
        with pytest.raises(MemoryConflictError):
            store.put(write, expected_revision=0)
        assert store.get(rows[0][0], scope).revision == 1
    else:
        assert rows == [] and events == []
        record = store.put(write, expected_revision=0)
        assert record.revision == 1
        assert len(store.events(scope)) == 1


def _occurrence_state(path):
    class NoDispatch:
        def execute(self, _call):
            raise AssertionError("backend must never execute")

    call = ToolCall("inert", "fixture.write", "disconnected", {"test": 1})
    registry = ToolRegistry((ToolRegistration(
        "inert", "fixture.write", Effect.WRITE, "mock", NoDispatch(),
    ),))
    token = OneShotAuthorization("hard-exit-fixture-token", call.request_id, 1000)
    return SyntheticOccurrenceStore(path), registry, call, token


def test_occurrence_hard_exit_after_commit_cannot_reuse_token(tmp_path):
    path = tmp_path / "occurrences.sqlite3"
    _hard_exit(_OCCURRENCE_CHILD, path, expected=43)
    store, registry, call, token = _occurrence_state(path)
    assert store.count_synthetic() == 1
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT token_digest, occurrence_id FROM synthetic_occurrence_reservations"
        ).fetchall()
    assert len(rows) == 1
    assert len(rows[0][0]) == 64
    assert rows[0][0] != token.token_id
    assert rows[0][1] == "occ_" + "a" * 64
    for occurrence_id in ("occ_" + "a" * 64, "occ_" + "b" * 64):
        with pytest.raises(SyntheticReplayRejected, match="already reserved"):
            store.reserve_synthetic(
                registry, call, token, occurrence_id=occurrence_id, now_ms=11,
            )
    assert store.count_synthetic() == 1


def test_proactive_hard_exit_after_commit_does_not_duplicate_marker(tmp_path):
    path = tmp_path / "proactive.sqlite3"
    _hard_exit(_PROACTIVE_CHILD, path, expected=44)
    ledger = SyntheticProactiveLedger(path)
    assert ledger.count() == 1
    policy = SyntheticTriggerPolicy(
        "fixture-owner", "notes", "fixture-event", 1, "fixture-v1", 100, 1000, 1,
    )
    with pytest.raises(SyntheticTriggerRejected, match="minimum preparation interval"):
        ledger.prepare(
            policy, source_digest="a" * 64, observation_digest="b" * 64,
            observed_at_ms=1000, now_ms=1001,
        )
    assert ledger.count() == 1
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT trigger_id FROM synthetic_prepared_triggers"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][0].startswith("trigger_")
