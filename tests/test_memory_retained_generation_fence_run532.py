"""Detached Memory generation comparison remains non-authorizing and read-only."""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import cas_generation_review as generation
from ark.memory import retained_generation_fence as fence


def _fixture(tmp_path):
    path = tmp_path / "synthetic-memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("owner-fixture", "private")
    write = MemoryWrite(scope, "fixed-synthetic-source", "initial")
    item = store.put(write, expected_revision=0)
    retained = generation.review_memory_revision_reuse(
        store, scope, write.source_id, expected_revision=1,
    )
    return path, store, scope, write.source_id, item, retained


def _check(retained, store, scope, source_id, revision=1):
    return fence.verify_retained_memory_generation(
        retained, store, scope, source_id, expected_revision=revision,
    )


def test_exact_retained_observation_survives_restart_without_write(tmp_path):
    path, store, scope, source, item, retained = _fixture(tmp_path)
    before = [(event.event_id, event.operation) for event in store.events(scope)]
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    assert _check(retained, reopened, scope, source) is None
    assert reopened.get(item.memory_id, scope).content == "initial"
    assert [(e.event_id, e.operation) for e in store.events(scope)] == before
    assert retained.write_authorized is False
    assert retained.erase_authorized is False
    assert retained.generation_authenticated is False


def test_cross_handle_update_changes_retained_event_epoch(tmp_path):
    path, store, scope, source, item, retained = _fixture(tmp_path)
    other = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    other.put(MemoryWrite(scope, source, "updated"), expected_revision=1)
    with pytest.raises(fence.RetainedMemoryGenerationRejected, match="changed"):
        _check(retained, store, scope, source)
    assert store.get(item.memory_id, scope).revision == 2


def test_delete_recreate_same_id_and_revision_does_not_pass_aba(tmp_path):
    path, store, scope, source, item, retained = _fixture(tmp_path)
    assert store.delete(item.memory_id, scope, expected_revision=1)
    restarted = SQLiteMemoryStore(path, clock_ms=lambda: 3000)
    new_item = restarted.put(
        MemoryWrite(scope, source, "second lifetime"), expected_revision=0,
    )
    assert new_item.memory_id == item.memory_id
    assert new_item.revision == item.revision == 1
    with pytest.raises(fence.RetainedMemoryGenerationRejected, match="changed"):
        _check(retained, restarted, scope, source)
    assert restarted.get(item.memory_id, scope).content == "second lifetime"


def test_terminal_delete_cannot_reuse_live_observation(tmp_path):
    _, store, scope, source, item, retained = _fixture(tmp_path)
    assert store.delete(item.memory_id, scope, expected_revision=1)
    with pytest.raises(fence.RetainedMemoryGenerationRejected, match="changed"):
        _check(retained, store, scope, source)


@pytest.mark.parametrize("field,value", (
    ("retained_history_sha256", "0" * 64),
    ("retained_history_sha256", "not-a-hash"),
    ("event_count", True),
    ("generation_count", -1),
    ("live_revision", 1.0),
    ("revision_reuse_possible", 1),
    ("expected_revision", 2),
    ("memory_id", "mem_" + "f" * 64),
))
def test_forged_retained_carrier_cannot_authorize_revalidation(
    tmp_path, field, value,
):
    _, store, scope, source, _, retained = _fixture(tmp_path)
    object.__setattr__(retained, field, value)
    with pytest.raises(fence.RetainedMemoryGenerationRejected):
        _check(retained, store, scope, source)


@pytest.mark.parametrize("revision", (True, 1.0, -1, 2**63, 2))
def test_fence_revision_input_must_match_exact_type_and_retained_revision(
    tmp_path, revision,
):
    _, store, scope, source, _, retained = _fixture(tmp_path)
    with pytest.raises(fence.RetainedMemoryGenerationRejected, match="revision"):
        _check(retained, store, scope, source, revision=revision)


def test_wrong_scope_or_source_cannot_pass_retained_generation(tmp_path):
    _, store, scope, source, _, retained = _fixture(tmp_path)
    wrong_scope = MemoryScope(scope.owner_id, "different")
    with pytest.raises(fence.RetainedMemoryGenerationRejected, match="changed"):
        _check(retained, store, wrong_scope, source)
    with pytest.raises(fence.RetainedMemoryGenerationRejected, match="changed"):
        _check(retained, store, scope, "different source")


def test_denial_callback_cannot_mutate_retained_hash_then_return_false(
    tmp_path, monkeypatch,
):
    _, store, scope, source, _, retained = _fixture(tmp_path)
    original = generation.MemoryGenerationReview.generation_authenticated

    def falsifying_getter(self):
        if self is retained:
            object.__setattr__(self, "retained_history_sha256", "0" * 64)
        return False

    monkeypatch.setattr(
        generation.MemoryGenerationReview,
        "generation_authenticated",
        property(falsifying_getter),
    )
    with pytest.raises(fence.RetainedMemoryGenerationRejected, match="changed"):
        _check(retained, store, scope, source)
    monkeypatch.setattr(
        generation.MemoryGenerationReview, "generation_authenticated", original,
    )


def test_memory_history_tamper_is_not_accepted_as_retained_epoch(
    tmp_path,
):
    path, store, scope, source, item, retained = _fixture(tmp_path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE memory_events SET revision=9 WHERE memory_id=?",
            (item.memory_id,),
        )
    with pytest.raises(fence.RetainedMemoryGenerationRejected):
        _check(retained, store, scope, source)


def test_arbitrary_object_is_not_a_retained_generation_report(tmp_path):
    _, store, scope, source, _, _ = _fixture(tmp_path)
    with pytest.raises(fence.RetainedMemoryGenerationRejected, match="exact"):
        _check(object(), store, scope, source)
