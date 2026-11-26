"""Detached Memory generation review rejects substituted callbacks before private reads.

Synthetic local SQLite only: a valid comparison is not consent, provenance,
an authenticated epoch or permission to write/erase Memory.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import cas_generation_review as generation
from ark.memory import retained_generation_fence as fence


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "retained-generation.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "notes")
    store.put(MemoryWrite(scope, "source", "private local value"))
    retained = generation.review_memory_revision_reuse(
        store, scope, "source", expected_revision=1,
    )
    return store, scope, retained


@pytest.mark.parametrize(
    ("member", "replacement"),
    (
        ("memory_id", "field"),
        ("retained_history_sha256", "field"),
        ("__getattribute__", "hook"),
        ("__init__", "hook"),
        ("generation_authenticated", "denial"),
    ),
)
def test_rebound_retained_review_descriptors_never_run(
    tmp_path, monkeypatch, member, replacement,
):
    store, scope, retained = _fixture(tmp_path)
    executed = []

    def rogue(*_args, **_kwargs):
        executed.append(member)
        pytest.fail("rebound retained callback accessed private report")

    if replacement == "field":
        new = property(rogue)
    elif replacement == "denial":
        new = property(rogue)
    else:
        new = rogue
    monkeypatch.setattr(generation.MemoryGenerationReview, member, new)

    with pytest.raises(
        fence.RetainedMemoryGenerationRejected,
        match="authority descriptor changed",
    ):
        fence.verify_retained_memory_generation(
            retained, store, scope, "source", expected_revision=1,
        )
    assert executed == []


def test_rebound_review_function_never_receives_private_memory_store(
    tmp_path, monkeypatch,
):
    store, scope, retained = _fixture(tmp_path)
    executed = []

    def rogue(*_args, **_kwargs):
        executed.append("private store")
        pytest.fail("substituted review callback must not be dispatched")

    monkeypatch.setattr(fence, "review_memory_revision_reuse", rogue)
    with pytest.raises(
        fence.RetainedMemoryGenerationRejected,
        match="authority descriptor changed",
    ):
        fence.verify_retained_memory_generation(
            retained, store, scope, "source", expected_revision=1,
        )
    assert executed == []


def test_original_retained_generation_still_verifies_without_authority(tmp_path):
    store, scope, retained = _fixture(tmp_path)
    assert fence.verify_retained_memory_generation(
        retained, store, scope, "source", expected_revision=1,
    ) is None
    assert retained.generation_authenticated is False
    assert retained.write_authorized is False
    assert retained.erase_authorized is False
