"""Retained Memory CAS comparison must reject parser drift before private reads.

Synthetic local SQLite proof never authorizes mutation, consent or replay.
"""

from __future__ import annotations

import re

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import cas_generation_review as generation
from ark.memory import retained_generation_fence as fence


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "retained-parser.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "notes")
    store.put(MemoryWrite(scope, "source", "private fixture text"))
    retained = generation.review_memory_revision_reuse(
        store, scope, "source", expected_revision=1,
    )
    return store, scope, retained


@pytest.mark.parametrize("surface", (
    "sha_parser", "id_parser", "event_budget", "sqlite_bound",
    "field_reader", "denial_validator",
))
def test_retained_generation_rejects_rebound_helper_without_private_store(
    tmp_path, monkeypatch, surface,
):
    store, scope, retained = _fixture(tmp_path)
    called = []

    def hostile(*_args, **_kwargs):
        called.append(surface)
        raise AssertionError("forged parser read private CAS observation")

    with monkeypatch.context() as patch:
        if surface == "sha_parser":
            patch.setattr(fence, "_SHA", re.compile(".*"))
        elif surface == "id_parser":
            patch.setattr(fence, "_ID", re.compile(".*"))
        elif surface == "event_budget":
            patch.setattr(fence, "_MAX_EVENTS", fence._MAX_EVENTS + 1)
        elif surface == "sqlite_bound":
            patch.setattr(fence, "SQLITE_INT_MAX", fence.SQLITE_INT_MAX - 1)
        elif surface == "field_reader":
            patch.setattr(fence, "_fields", hostile)
        else:
            patch.setattr(fence, "_assert_original_denials", hostile)
        with pytest.raises(
            fence.RetainedMemoryGenerationRejected,
            match="parser or review helper changed",
        ):
            fence.verify_retained_memory_generation(
                retained, store, scope, "source", expected_revision=1,
            )
    assert called == []
    assert retained.write_authorized is False


def test_original_retained_generation_still_completes_deny_only(tmp_path):
    store, scope, retained = _fixture(tmp_path)
    assert fence.verify_retained_memory_generation(
        retained, store, scope, "source", expected_revision=1,
    ) is None
    assert retained.generation_authenticated is False
    assert retained.write_authorized is False
    assert retained.erase_authorized is False
