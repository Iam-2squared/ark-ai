"""Retained Memory CAS witness must describe a possible event lifecycle.

This is offline, fail-closed input geometry; no writer attribution or retry.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import cas_generation_review as generation
from ark.memory import retained_generation_fence as fence


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "synthetic-memory.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("fixture-owner", "notes")
    source = "fixture-source"
    store.put(MemoryWrite(scope, source, "private synthetic content"))
    retained = generation.review_memory_revision_reuse(
        store, scope, source, expected_revision=1,
    )
    return store, scope, source, retained


@pytest.mark.parametrize("changes", (
    {"event_count": 0, "generation_count": 0, "live_revision": 1},
    {"event_count": 1, "generation_count": 0, "live_revision": None},
    {"event_count": 1, "generation_count": 1, "live_revision": None},
    {
        "event_count": 2, "generation_count": 2, "live_revision": 1,
        "revision_reuse_possible": True,
    },
    {
        "event_count": 3, "generation_count": 2, "live_revision": 2,
        "revision_reuse_possible": True,
    },
    {"event_count": 1, "generation_count": 1, "live_revision": 2},
    {"event_count": 3, "generation_count": 3, "live_revision": None},
))
def test_impossible_retained_lifetime_is_refused_before_private_sqlite(
    tmp_path, monkeypatch, changes,
):
    store, scope, source, retained = _fixture(tmp_path)
    forged = replace(retained, **changes)
    accessed = []

    def forbidden_read():
        accessed.append(True)
        raise AssertionError("retained input should be rejected before SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect_readonly", forbidden_read)
        with pytest.raises(
            fence.RetainedMemoryGenerationRejected,
            match="invalid retained generation fields",
        ):
            fence.verify_retained_memory_generation(
                forged, store, scope, source, expected_revision=1,
            )
    assert accessed == []
    assert retained.write_authorized is False
    assert retained.generation_authenticated is False


@pytest.mark.parametrize("terminal", (False, True))
def test_possible_multi_lifetime_geometry_remains_read_only(tmp_path, terminal):
    store, scope, source, _ = _fixture(tmp_path)
    first = store.get(
        generation.deterministic_memory_id(scope, source), scope,
    )
    assert first is not None
    assert store.delete(first.memory_id, scope, expected_revision=1)
    second = store.put(MemoryWrite(scope, source, "second lifetime"))
    if terminal:
        assert store.delete(second.memory_id, scope, expected_revision=1)
    else:
        store.put(
            MemoryWrite(scope, source, "updated second lifetime"),
            expected_revision=1,
        )
    retained = generation.review_memory_revision_reuse(
        store, scope, source, expected_revision=1 if terminal else 2,
    )
    assert retained.generation_count == 2
    assert retained.event_count == 4
    assert retained.live_revision is (None if terminal else 2)
    assert fence.verify_retained_memory_generation(
        retained, store, scope, source,
        expected_revision=1 if terminal else 2,
    ) is None
    assert retained.write_authorized is False
    assert retained.erase_authorized is False
