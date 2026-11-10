"""Cold-restart review after a generation CAS returned COMMIT-UNKNOWN.

Child's local UPDATE commits, then a deliberately failed readback prevents
success attribution. Parent never retries; independent local recovery only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.generation_cas_outcome_review import (
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)

_CHILD = """
import sqlite3
import sys
from pathlib import Path
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected, MemoryGenerationCASToken,
    generation_fenced_memory_update,
)
path = Path(sys.argv[1])
scope = MemoryScope("owner", "private")
store = SQLiteMemoryStore(path, clock_ms=lambda: 200)
token = MemoryGenerationCASToken(
    sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]),
    sys.argv[6], sys.argv[7],
)
def unreadable():
    raise sqlite3.OperationalError("synthetic postcommit power loss")
store._connect_readonly = unreadable
try:
    generation_fenced_memory_update(
        store, MemoryWrite(scope, "source", "after"),
        retained=token,
    )
except MemoryGenerationCASRejected as error:
    assert "post-COMMIT readback" in str(error), str(error)
    print("UNKNOWN", flush=True)
else:
    raise AssertionError("postcommit readback failure must not return success")
"""


@pytest.mark.parametrize("later_write", (False, True))
def test_unknown_commit_survives_restarted_process_without_auto_retry(
    tmp_path: Path, later_write: bool,
) -> None:
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("owner", "private")
    original_store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    initial = original_store.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(
        original_store, scope, "source",
    )
    fields = (
        retained.memory_id, str(retained.create_event_id),
        str(retained.last_event_id), str(retained.revision),
        retained.event_prefix_sha256, retained.row_sha256,
    )
    process = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path), *fields],
        capture_output=True, text=True, timeout=45, check=False,
    )
    assert process.returncode == 0, (process.stdout, process.stderr)
    assert process.stdout.strip() == "UNKNOWN"
    proposal = MemoryWrite(scope, "source", "after")
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 201)
    committed = cold.get(initial.memory_id, scope)
    assert committed is not None
    assert committed.content == "after"
    assert committed.revision == 2

    if later_write:
        # A second local writer advances the same lifetime before the
        # original observer starts. Matching initial bytes cannot prove who
        # committed the first UPDATE.
        next_token = observe_memory_generation_for_cas(cold, scope, "source")
        second = generation_fenced_memory_update(
            SQLiteMemoryStore(path, clock_ms=lambda: 202),
            MemoryWrite(scope, "source", "different-later"),
            retained=next_token,
        )
        assert second.revision == 3

    review = review_memory_generation_cas_outcome(
        SQLiteMemoryStore(path, clock_ms=lambda: 203),
        proposal, retained=retained,
    )
    assert review.observation == (
        "DIVERGED_OBSERVED" if later_write
        else "ONE_MATCHING_UPDATE_OBSERVED"
    )
    assert review.commit_attributed_to_caller is False
    assert review.automatic_retry_authorized is False
    assert review.external_action_authorized is False
    assert review.consent_authenticated is False
    assert review.trusted_clock_verified is False
    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            cold, proposal, retained=retained,
        )
    events = cold.events(scope)
    assert [(event.operation, event.revision) for event in events] == (
        [("create", 1), ("update", 2), ("update", 3)]
        if later_write else [("create", 1), ("update", 2)]
    )
