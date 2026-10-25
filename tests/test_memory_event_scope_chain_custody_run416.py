"""A synthetic Memory event witness cannot hide input or chain-link drift."""

import sys
from pathlib import Path

import pytest

import ark.memory.synthetic_event_continuity_review as continuity
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path: Path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    return memory, scope


def _clone(value: str) -> str:
    new = (" " + value)[1:]
    assert new == value and new is not value
    return new


@pytest.mark.parametrize("field", ("owner_id", "namespace"))
@pytest.mark.parametrize("stage", (
    "ARK-synthetic-memory-event-scope-v1",
    "ARK-synthetic-memory-event-genesis-v1",
))
def test_first_digest_callbacks_must_preserve_original_scope_carriers(
    tmp_path: Path, monkeypatch, field, stage,
):
    memory, scope = _fixture(tmp_path)
    original_hash = continuity._hash

    def hash_then_swap(label, values):
        result = original_hash(label, values)
        if label == stage:
            object.__setattr__(scope, field, _clone(getattr(scope, field)))
        return result

    monkeypatch.setattr(continuity, "_hash", hash_then_swap)
    with pytest.raises(
        continuity.SyntheticMemoryEventRejected, match="scope changed",
    ):
        continuity.review_synthetic_memory_event_continuity(memory, scope)


@pytest.mark.parametrize("field", ("scope_digest", "tail_hash"))
def test_retained_witness_shape_callback_cannot_rebaseline_equal_carrier(
    tmp_path: Path, monkeypatch, field,
):
    memory, scope = _fixture(tmp_path)
    retained = continuity.review_synthetic_memory_event_continuity(memory, scope)
    original_shape = continuity.SyntheticMemoryEventWitness.assert_shape

    def shape_and_swap(self, digest):
        original_shape(self, digest)
        if self is retained:
            object.__setattr__(self, field, _clone(getattr(self, field)))

    monkeypatch.setattr(
        continuity.SyntheticMemoryEventWitness, "assert_shape", shape_and_swap,
    )
    with pytest.raises(
        continuity.SyntheticMemoryEventRejected, match="retained Memory witness changed",
    ):
        continuity.review_synthetic_memory_event_continuity(
            memory, scope, retained=retained,
        )


def test_digest_callback_cannot_corrupt_previous_event_witness(
    tmp_path: Path, monkeypatch,
):
    memory, scope = _fixture(tmp_path)
    memory.put(MemoryWrite(scope, "source", "LOCAL-FIXTURE"))
    original_hash = continuity._hash

    def change_prior(label, values):
        if label == "ARK-synthetic-memory-event-v1":
            previous = sys._getframe(1).f_locals["prior"]
            object.__setattr__(previous, "tail_hash", "memevt_" + "f" * 64)
        return original_hash(label, values)

    monkeypatch.setattr(continuity, "_hash", change_prior)
    with pytest.raises(
        continuity.SyntheticMemoryEventRejected, match="prior Memory event chain link",
    ):
        continuity.review_synthetic_memory_event_continuity(memory, scope)


def test_clean_memory_event_prefix_remains_local_and_non_authoritative(tmp_path: Path):
    memory, scope = _fixture(tmp_path)
    memory.put(MemoryWrite(scope, "source", "LOCAL-FIXTURE"))
    first = continuity.review_synthetic_memory_event_continuity(memory, scope)
    second = continuity.review_synthetic_memory_event_continuity(
        memory, scope, retained=first,
    )
    assert first == second
    assert first.event_count == 1
    assert not second.context_use_authorized
    assert not second.deletion_authorized
    assert not second.external_disclosure_authorized
