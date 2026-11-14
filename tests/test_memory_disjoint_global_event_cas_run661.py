"""Generation-fenced Memory CAS ignores disjoint SQLite event append epochs.

One database may serve several owners, namespaces and source IDs. An
independent event must not be mistaken for a mutation of the target lifetime;
no CAS token is approval, an issuer identity, or permission to act externally.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_event_alignment import review_memory_event_alignment


@pytest.mark.parametrize(
    "disjoint",
    ("other_owner", "other_namespace", "other_source_same_scope"),
)
def test_disjoint_second_handle_event_does_not_invalidate_target_generation(
    tmp_path, disjoint,
):
    path = tmp_path / "disjoint-event-cas.sqlite"
    scope = MemoryScope("fixture-owner", "private")
    original = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    created = original.put(
        MemoryWrite(scope, "source-target", "before"), expected_revision=0,
    )
    retained = observe_memory_generation_for_cas(
        original, scope, "source-target",
    )
    assert retained.last_event_id == 1

    if disjoint == "other_owner":
        other_scope = MemoryScope("different-owner", "private")
        other_source = "source-target"
    elif disjoint == "other_namespace":
        other_scope = MemoryScope("fixture-owner", "other-private-namespace")
        other_source = "source-target"
    else:
        other_scope = scope
        other_source = "another-source"

    independent = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    side = independent.put(
        MemoryWrite(other_scope, other_source, "side-event"),
        expected_revision=0,
    )
    assert side.memory_id != created.memory_id
    latest_before = observe_memory_generation_for_cas(
        original, scope, "source-target",
    )
    # Row-generation evidence concerns one target even while the global
    # append sequence has independently advanced.
    assert latest_before == retained

    target_writer = SQLiteMemoryStore(path, clock_ms=lambda: 3000)
    result = generation_fenced_memory_update(
        target_writer, MemoryWrite(scope, "source-target", "after"),
        retained=retained,
    )
    assert result.memory_id == created.memory_id
    assert (result.revision, result.content) == (2, "after")
    fresh = observe_memory_generation_for_cas(
        target_writer, scope, "source-target",
    )
    assert fresh.create_event_id == retained.create_event_id
    assert fresh.last_event_id == 3
    assert fresh.event_prefix_sha256 != retained.event_prefix_sha256
    assert fresh.external_action_authorized is False
    assert fresh.consent_authenticated is False
    assert independent.get(side.memory_id, other_scope) == side

    alignment = review_memory_event_alignment(target_writer)
    assert (alignment.row_count, alignment.event_count, alignment.last_event_id) == (
        2, 3, 3,
    )
    assert alignment.action_authorized is False
