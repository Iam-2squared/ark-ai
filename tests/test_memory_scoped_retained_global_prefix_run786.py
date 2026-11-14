"""Scoped Memory reviews bind foreign-owner payloads to a retained global prefix.

Only disposable synthetic SQLite fixtures are changed. Local witnesses are
not authenticated provenance, independent custody, or privacy permission.
"""

import sqlite3
from dataclasses import replace

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_event_prefix_review import (
    capture_local_memory_event_prefix,
)
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.memory.synthetic_multiscope_integrity_review import (
    SyntheticMemorySnapshotRejected,
    review_synthetic_memory_scopes,
)


def _setup(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "global-retained.sqlite", clock_ms=lambda: 100,
    )
    chosen = MemoryScope("chosen-owner", "chosen")
    foreign = MemoryScope("foreign-owner", "hidden")
    store.put(MemoryWrite(chosen, "chosen-source", "private chosen"))
    store.put(MemoryWrite(foreign, "foreign-source", "private foreign"))
    return store, chosen, foreign


@pytest.mark.parametrize(
    ("column", "value"),
    (("occurred_at_ms", 101), ("operation", "update")),
)
def test_foreign_payload_rewrite_is_detected_only_with_retained_witness(
    tmp_path, column, value,
):
    store, chosen, foreign = _setup(tmp_path)
    witness = capture_local_memory_event_prefix(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            f"UPDATE memory_events SET {column}=? WHERE owner_id=?",
            (value, foreign.owner_id),
        )
    # No foreign row is hydrated; current global high-water still looks fine.
    without = review_synthetic_memory_scopes(store, (chosen,))
    assert without.context_use_authorized is False
    with pytest.raises(
        SyntheticMemorySnapshotRejected, match="global Memory event prefix",
    ):
        review_synthetic_memory_scopes(
            store, (chosen,), retained_global_prefix=witness,
        )


def test_append_after_retained_global_prefix_is_permitted(tmp_path):
    store, chosen, foreign = _setup(tmp_path)
    witness = capture_local_memory_event_prefix(store)
    first = review_synthetic_memory_scopes(
        store, (chosen,), retained_global_prefix=witness,
    )
    store.put(MemoryWrite(foreign, "second", "another private record"))
    later = review_synthetic_memory_scopes(
        store, (chosen,), retained_global_prefix=witness,
    )
    assert later.snapshot_digest == first.snapshot_digest
    assert later.scopes[0].events.event_count == 1
    assert later.external_disclosure_authorized is False


def test_retained_global_prefix_rejects_coordinated_tail_rollback(tmp_path):
    store, chosen, foreign = _setup(tmp_path)
    witness = capture_local_memory_event_prefix(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "DELETE FROM memories WHERE owner_id=?", (foreign.owner_id,),
        )
        conn.execute(
            "DELETE FROM memory_events WHERE owner_id=?", (foreign.owner_id,),
        )
        conn.execute(
            "UPDATE sqlite_sequence SET seq=1 WHERE name='memory_events'"
        )
    # COUNT/MIN/MAX/sequence are consistent, but the retained global
    # snapshot still proves the local tip cannot be treated as unchanged.
    with pytest.raises(SyntheticMemorySnapshotRejected, match="rolled back"):
        review_synthetic_memory_scopes(
            store, (chosen,), retained_global_prefix=witness,
        )


def test_noncanonical_retained_global_witness_is_refused(tmp_path):
    store, chosen, _ = _setup(tmp_path)
    witness = capture_local_memory_event_prefix(store)
    forged = replace(witness, event_count=True)
    with pytest.raises(
        SyntheticMemorySnapshotRejected, match="invalid retained global",
    ):
        review_synthetic_memory_scopes(
            store, (chosen,), retained_global_prefix=forged,
        )
