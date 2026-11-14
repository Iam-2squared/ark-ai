"""A coherent Memory v1 read must not mix cross-process namespace commits.

The writer is a separate local Python process and can commit while the
reviewer's single read-only SQLite transaction is open. All data are fixtures;
no connected personal data, remote service, or external Tool is used.
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

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

path = pathlib.Path(sys.argv[1])
mode = sys.argv[2]
writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
for name in ("alpha", "beta"):
    scope = MemoryScope("isolated-owner", name)
    if mode == "insert":
        write = MemoryWrite(scope, "new-source", "new-" + name)
        saved = writer.put(write)
        assert saved.revision == 1
    elif mode == "update":
        write = MemoryWrite(scope, "base-source", "changed-" + name)
        saved = writer.put(write, expected_revision=1)
        assert saved.revision == 2
    else:
        raise AssertionError("unknown writer mode")
print("COMMITTED", flush=True)
"""


@pytest.mark.parametrize("mode", ("insert", "update"))
def test_one_snapshot_remains_at_old_epoch_across_two_child_commits(
    tmp_path, mode,
):
    path = tmp_path / "two-scopes.sqlite"
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    for name in ("alpha", "beta"):
        reader.put(MemoryWrite(
            MemoryScope("isolated-owner", name), "base-source",
            "before-" + name,
        ))

    request = CoherentSnapshotRequest(
        "isolated-owner", ("alpha", "beta"), per_namespace_limit=5,
    )
    spawned = []

    def clock_during_open_snapshot():
        completed = subprocess.run(
            [sys.executable, "-c", _CHILD, str(path), mode],
            capture_output=True, text=True, timeout=35, check=True,
        )
        assert completed.stdout.strip() == "COMMITTED", completed.stderr
        spawned.append(completed.returncode)
        return 150

    # The review first anchors the read transaction (including its first
    # SELECT) and only then calls the clock, where the other process commits.
    reader._clock_ms = clock_during_open_snapshot
    frozen = review_coherent_snapshot(reader, request)
    assert spawned == [0]
    assert frozen.read_at_ms == 150
    assert [tuple(record.content for record in group) for group in frozen.records] == [
        ("before-alpha",), ("before-beta",),
    ]

    # A new transaction can see the child's commits. The prior coherent
    # witness must not retroactively mix these later rows into its digest.
    after = review_coherent_snapshot(
        SQLiteMemoryStore(path, clock_ms=lambda: 150), request,
    )
    assert after.provenance_sha256 != frozen.provenance_sha256
    expected_count = 2 if mode == "insert" else 1
    assert [len(group) for group in after.records] == [
        expected_count, expected_count,
    ]
    for name, group in zip(("alpha", "beta"), after.records, strict=True):
        assert any(record.content.endswith(name) and (
            record.content.startswith("new-")
            if mode == "insert" else record.content.startswith("changed-")
        ) for record in group)
    assert not hasattr(frozen, "dispatch_authorized")
