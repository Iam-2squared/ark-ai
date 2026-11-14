"""Post-denial retention of one SQLite Memory row/event snapshot result.

These checks only operate on disposable local fixtures and never prove a
historical writer, external consent, disclosure, or cross-store atomicity.
"""

from pathlib import Path

import pytest

import ark.memory.atomic_epoch_review as atomic
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "memory-atomic-final.sqlite3",
        clock_ms=lambda: 2000,
    )
    scope = MemoryScope("test-owner", "synthetic-notes")
    store.put(MemoryWrite(
        scope, "fixture-source", "private synthetic text",
    ))
    return store, scope


def test_stable_single_transaction_result_remains_inert(tmp_path):
    store, scope = _case(tmp_path)
    a = atomic.review_atomic_memory_epoch(store, (scope,))
    b = atomic.review_atomic_memory_epoch(store, (scope,))
    assert a == b
    assert a.row_counts == (1,)
    assert a.event_counts == (1,)
    assert a.independent_writer_proven is False
    assert a.cross_store_atomicity_proven is False
    assert a.trusted_clock_proven is False
    assert a.memory_disclosure_authorized is False
    assert a.dispatch_authorized is False
    assert "private synthetic text" not in repr(a)


@pytest.mark.parametrize(
    "target",
    (
        "scope_fingerprints",
        "row_counts",
        "event_counts",
        "event_tail_ids",
        "epoch_digest",
        "content_digest",
    ),
)
def test_final_false_denial_getter_cannot_change_witness_fields(
    tmp_path, monkeypatch, target,
):
    store, scope = _case(tmp_path)
    called = []

    def change_after_last_check(witness):
        called.append(True)
        value = getattr(witness, target)
        if type(value) is tuple:
            replacement = tuple(list(value))
            assert replacement == value and replacement is not value
        else:
            replacement = ("x" + value)[1:]
            assert replacement == value and replacement is not value
        object.__setattr__(witness, target, replacement)
        return False

    monkeypatch.setattr(
        atomic.AtomicMemoryEpochReview, "dispatch_authorized",
        property(change_after_last_check),
    )
    with pytest.raises(MemorySchemaError, match="after denial"):
        atomic.review_atomic_memory_epoch(store, (scope,))
    assert called


@pytest.mark.parametrize("target", ("source", "scope"))
def test_last_denial_cannot_retarget_original_sqlite_snapshot_inputs(
    tmp_path, monkeypatch, target,
):
    store, scope = _case(tmp_path)

    def change_after_last_check(_witness):
        if target == "source":
            initial = store.path
            replacement = Path(str(initial))
            assert replacement == initial and replacement is not initial
            store.path = replacement
        else:
            object.__setattr__(scope, "namespace", "substituted-notes")
        return False

    monkeypatch.setattr(
        atomic.AtomicMemoryEpochReview, "dispatch_authorized",
        property(change_after_last_check),
    )
    with pytest.raises(MemorySchemaError, match="changed during review"):
        atomic.review_atomic_memory_epoch(store, (scope,))


def test_final_denial_mutation_to_privilege_is_not_accepted(tmp_path, monkeypatch):
    store, scope = _case(tmp_path)

    def mutate_property(_witness):
        monkeypatch.setattr(
            atomic.AtomicMemoryEpochReview, "independent_writer_proven",
            property(lambda _: True),
        )
        return False

    monkeypatch.setattr(
        atomic.AtomicMemoryEpochReview, "dispatch_authorized",
        property(mutate_property),
    )
    with pytest.raises(MemorySchemaError, match="gained authority"):
        atomic.review_atomic_memory_epoch(store, (scope,))
