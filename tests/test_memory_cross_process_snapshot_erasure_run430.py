"""Coherent Memory reads stay at one epoch while an independent process erases.

Each scenario touches only disposable local SQLite data. A read-only snapshot
is not a privacy erasure authorization and cannot attest any external effect.
"""

import subprocess
import sys

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)

_CHILD = r"""
import pathlib
import sys

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.memory.sqlite_store import deterministic_memory_id

path = pathlib.Path(sys.argv[1])
mode = sys.argv[2]
store = SQLiteMemoryStore(path, clock_ms=lambda: 200)
for namespace in ("alpha", "beta"):
    scope = MemoryScope("isolated-owner", namespace)
    # Recompute the identity in this process; no Memory object is shared
    # between the writer and the already-anchored reader.
    memory_id = deterministic_memory_id(scope, "base-source")
    if mode == "delete":
        assert store.delete(memory_id, scope, expected_revision=1)
    elif mode == "purge":
        assert store.purge_expired(scope=scope) == 1
    else:
        raise AssertionError("unknown local erasure mode")
print("ERASED", flush=True)
"""


@pytest.mark.parametrize("mode", ("delete", "purge"))
def test_single_snapshot_remains_pre_erasure_across_two_child_commits(tmp_path, mode):
    path = tmp_path / "coherent-erasure.sqlite"
    owner = "isolated-owner"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    for namespace in ("alpha", "beta"):
        store.put(MemoryWrite(
            MemoryScope(owner, namespace), "base-source",
            "before-" + namespace, expires_at_ms=160,
        ))
    request = CoherentSnapshotRequest(
        owner, ("alpha", "beta"), per_namespace_limit=5,
    )
    child_commits = []

    def clock_after_snapshot_anchor():
        done = subprocess.run(
            [sys.executable, "-c", _CHILD, str(path), mode],
            capture_output=True, text=True, timeout=35, check=True,
        )
        assert done.stdout.strip() == "ERASED", done.stderr
        child_commits.append(done.returncode)
        return 150

    store._clock_ms = clock_after_snapshot_anchor
    before = review_coherent_snapshot(store, request)
    assert child_commits == [0]
    assert before.read_at_ms == 150
    assert [
        tuple(record.content for record in group) for group in before.records
    ] == [("before-alpha",), ("before-beta",)]
    assert before.provenance_sha256

    after = review_coherent_snapshot(
        SQLiteMemoryStore(path, clock_ms=lambda: 150), request,
    )
    assert tuple(map(len, after.records)) == (0, 0)
    assert after.provenance_sha256 != before.provenance_sha256
    # A committed delete/expiry records one event for each namespace,
    # without retroactively changing the already anchored SQLite snapshot.
    ledger = SQLiteMemoryStore(path, clock_ms=lambda: 150)
    for namespace in ("alpha", "beta"):
        events = ledger.events(MemoryScope(owner, namespace))
        assert tuple(event.operation for event in events) == (
            "create", "delete" if mode == "delete" else "expire",
        )
