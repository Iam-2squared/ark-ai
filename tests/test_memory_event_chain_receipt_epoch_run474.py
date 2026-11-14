"""Synthetic Memory event witnesses retain historical carrier identity."""

from __future__ import annotations

import pytest

import ark.memory.synthetic_event_continuity_review as continuity
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "event-witness.sqlite3", clock_ms=lambda: 100)
    scope = MemoryScope("test-owner", "private")
    store.put(MemoryWrite(scope, "source", "synthetic-first"))
    return store, scope


def test_forged_constructor_cannot_inject_authorizing_result(tmp_path, monkeypatch):
    store, scope = _store(tmp_path)

    class Forged:
        deletion_authorized = True
        context_use_authorized = True
        external_disclosure_authorized = True

    monkeypatch.setattr(continuity, "SyntheticMemoryEventWitness", lambda *a: Forged())
    with pytest.raises(continuity.SyntheticMemoryEventRejected, match="constructed"):
        continuity.review_synthetic_memory_event_continuity(store, scope)
    assert store.events(scope)[0].operation == "create"


@pytest.mark.parametrize("field", ("scope_digest", "tail_hash"))
def test_equal_value_witness_string_rebinding_rejected(
    tmp_path, monkeypatch, field,
):
    store, scope = _store(tmp_path)
    original = continuity.SyntheticMemoryEventWitness

    def modified(*args):
        witness = original(*args)
        value = getattr(witness, field)
        replacement = "".join((value[:9], value[9:]))
        assert replacement == value and replacement is not value
        object.__setattr__(witness, field, replacement)
        return witness

    monkeypatch.setattr(continuity, "SyntheticMemoryEventWitness", modified)
    with pytest.raises(continuity.SyntheticMemoryEventRejected, match="constructed"):
        continuity.review_synthetic_memory_event_continuity(store, scope)


def test_earlier_witness_rewritten_after_next_link_rejected(tmp_path, monkeypatch):
    store, scope = _store(tmp_path)
    store.put(MemoryWrite(scope, "source", "synthetic-second"), expected_revision=1)
    original = continuity.SyntheticMemoryEventWitness
    observed = []

    def create(*args):
        witness = original(*args)
        observed.append(witness)
        if len(observed) == 3:
            object.__setattr__(observed[0], "tail_hash", "f" * 71)
        return witness

    monkeypatch.setattr(continuity, "SyntheticMemoryEventWitness", create)
    with pytest.raises(continuity.SyntheticMemoryEventRejected, match="earlier"):
        continuity.review_synthetic_memory_event_continuity(store, scope)
    assert len(store.events(scope)) == 2


def test_valid_retained_prefix_and_no_content_disclosure(tmp_path):
    store, scope = _store(tmp_path)
    first = continuity.review_synthetic_memory_event_continuity(store, scope)
    store.put(MemoryWrite(scope, "source", "synthetic-second"), expected_revision=1)
    next_witness = continuity.review_synthetic_memory_event_continuity(
        store, scope, retained=first,
    )
    assert next_witness.event_count == 2
    assert next_witness.last_event_id > first.last_event_id
    assert next_witness.deletion_authorized is False
    assert next_witness.context_use_authorized is False
    assert next_witness.external_disclosure_authorized is False
    assert "synthetic-second" not in repr(next_witness)
