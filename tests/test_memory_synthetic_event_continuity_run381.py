"""Bounded Memory v1 event continuity and independently retained witnesses."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.memory.synthetic_event_continuity_review import (
    SyntheticMemoryEventRejected,
    review_synthetic_memory_event_continuity,
)


def fixture(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "Memory # %.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("private-owner", "private-namespace")
    return store, scope


def put(state, content="PRIVATE-MEMORY", *, expected_revision=0):
    store, scope = state
    return store.put(
        MemoryWrite(scope, "source", content),
        expected_revision=expected_revision,
    )


def review(state, **options):
    return review_synthetic_memory_event_continuity(*state, **options)


def test_empty_and_written_store_never_authorizes_content_use(tmp_path: Path):
    state = fixture(tmp_path)
    empty = review(state)
    assert empty.event_count == 0
    assert empty.last_event_id == 0
    assert empty.deletion_authorized is False
    first = put(state)
    result = review(state)
    assert result.event_count == 1
    assert result.last_event_id > 0
    assert result.tail_hash != empty.tail_hash
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert first.memory_id not in repr(result)
    assert "PRIVATE-MEMORY" not in repr(result)


def test_retained_prefix_survives_valid_cas_update(tmp_path: Path):
    state = fixture(tmp_path)
    put(state)
    prior = review(state)
    put(state, "PRIVATE-CHANGED", expected_revision=1)
    value = review(state, retained=prior)
    assert value.event_count == 2
    assert value.last_event_id > prior.last_event_id


def test_recreated_memory_id_after_delete_is_new_lifecycle(tmp_path: Path):
    state = fixture(tmp_path)
    record = put(state)
    assert state[0].delete(record.memory_id, state[1], expected_revision=1)
    put(state, "PRIVATE-RECREATED", expected_revision=0)
    assert review(state).event_count == 3


def test_per_scope_event_id_gaps_from_other_owner_are_valid(tmp_path: Path):
    state = fixture(tmp_path)
    put(state)
    state[0].put(MemoryWrite(
        MemoryScope("unrelated-owner", "other"), "another", "OTHER-PRIVATE",
    ))
    put(state, "PRIVATE-UPDATED", expected_revision=1)
    witness = review(state)
    assert witness.event_count == 2
    assert witness.last_event_id == 3


def test_changed_live_revision_without_event_is_rejected(tmp_path: Path):
    state = fixture(tmp_path)
    put(state)
    with sqlite3.connect(state[0].path) as conn:
        conn.execute("UPDATE memories SET revision=2")
    with pytest.raises(SyntheticMemoryEventRejected, match="live rows"):
        review(state)


def test_new_live_row_without_corresponding_create_event_is_rejected(tmp_path: Path):
    state = fixture(tmp_path)
    put(state)
    with sqlite3.connect(state[0].path) as conn:
        conn.execute("DELETE FROM memory_events")
    with pytest.raises(SyntheticMemoryEventRejected, match="live rows"):
        review(state)


@pytest.mark.parametrize("sql", [
    "UPDATE memory_events SET revision=9",
    "UPDATE memory_events SET operation='update'",
    "UPDATE memory_events SET occurred_at_ms=-1",
])
def test_malformed_event_or_transition_is_rejected(tmp_path: Path, sql: str):
    state = fixture(tmp_path)
    put(state)
    with sqlite3.connect(state[0].path) as conn:
        conn.execute(sql)
    with pytest.raises(SyntheticMemoryEventRejected, match="invalid|malformed"):
        review(state)


def test_independent_prefix_detects_coherent_suffix_rollback(tmp_path: Path):
    state = fixture(tmp_path)
    put(state)
    prior = review(state)
    put(state, "PRIVATE-SECOND", expected_revision=1)
    latest = review(state)
    # Deliberately simulate a fully coherent *local* rewrite of both v1
    # event suffix and current row, on disposable synthetic test data only.
    with sqlite3.connect(state[0].path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=2")
        conn.execute(
            "UPDATE memories SET revision=1, content='PRIVATE-MEMORY',"
            " content_sha256=?",
            (hashlib.sha256(b"PRIVATE-MEMORY").hexdigest(),),
        )
    assert review(state, retained=prior).event_count == 1
    with pytest.raises(SyntheticMemoryEventRejected, match="retained"):
        review(state, retained=latest)


def test_synthetic_retained_witness_reflective_change_rejected(tmp_path: Path):
    state = fixture(tmp_path)
    put(state)
    witness = review(state)
    object.__setattr__(witness, "event_count", True)
    with pytest.raises(SyntheticMemoryEventRejected, match="invalid"):
        review(state, retained=witness)


@pytest.mark.parametrize("bad", [object(), True, "not-witness"])
def test_retained_witness_exact_type_required(tmp_path: Path, bad):
    state = fixture(tmp_path)
    put(state)
    with pytest.raises(SyntheticMemoryEventRejected, match="exact"):
        review(state, retained=bad)


def test_missing_initialized_db_is_not_created_by_review(tmp_path: Path):
    state = fixture(tmp_path)
    put(state)
    db = state[0].path
    db.rename(tmp_path / "moved.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        review(state)
    assert not db.exists()


def test_post_bootstrap_schema_change_is_rejected(tmp_path: Path):
    state = fixture(tmp_path)
    put(state)
    with sqlite3.connect(state[0].path) as conn:
        conn.execute("CREATE TABLE unexpected(k TEXT)")
    with pytest.raises(RuntimeError, match="schema"):
        review(state)


def test_scope_and_store_exact_types_are_required(tmp_path: Path):
    state = fixture(tmp_path)
    with pytest.raises(SyntheticMemoryEventRejected, match="exact"):
        review_synthetic_memory_event_continuity(state[0], "scope")
    with pytest.raises(SyntheticMemoryEventRejected, match="exact"):
        review_synthetic_memory_event_continuity(object(), state[1])
