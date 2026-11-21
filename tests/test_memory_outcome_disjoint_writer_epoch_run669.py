"""Read-only Memory COMMIT-UNKNOWN observations ignore disjoint writer epochs.

Unrelated SQLite events must not be credited to the retained caller or
mistaken for target-row mutation. All witnesses remain manual-only.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_cas_outcome_review import (
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas


@pytest.mark.parametrize(
    "variant",
    ("other_owner", "other_namespace", "other_source"),
)
@pytest.mark.parametrize("matching_target_update", (False, True))
def test_disjoint_event_does_not_retarget_ambiguous_cas_observation(
    tmp_path, variant, matching_target_update,
):
    path = tmp_path / "disjoint-ambiguous.sqlite"
    scope = MemoryScope("private-owner", "local")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    observer = SQLiteMemoryStore(path, clock_ms=lambda: 300)
    original = writer.put(
        MemoryWrite(scope, "target", "old", expires_at_ms=5000),
        expected_revision=0,
    )
    retained = observe_memory_generation_for_cas(writer, scope, "target")
    proposed = MemoryWrite(
        scope, "target", "next", {"privacy": "synthetic"},
        expires_at_ms=4000,
    )

    if variant == "other_owner":
        other_scope = MemoryScope("another-owner", "local")
        other_source = "target"
    elif variant == "other_namespace":
        other_scope = MemoryScope("private-owner", "another-namespace")
        other_source = "target"
    else:
        other_scope = scope
        other_source = "unrelated"

    side = observer.put(
        MemoryWrite(other_scope, other_source, "disjoint"),
        expected_revision=0,
    )
    assert side.memory_id != original.memory_id
    if matching_target_update:
        # A different handle, not the reviewing caller, committed exact bytes.
        observer.put(proposed, expected_revision=1)

    prior_events = writer.events(scope)
    result = review_memory_generation_cas_outcome(
        writer, proposed, retained=retained,
    )
    assert result.observation == (
        "ONE_MATCHING_UPDATE_OBSERVED"
        if matching_target_update else "UNCHANGED_OBSERVED"
    )
    assert (result.observed_prefix_sha256 != retained.event_prefix_sha256) is (
        matching_target_update
    )
    assert result.commit_attributed_to_caller is False
    assert result.automatic_retry_authorized is False
    assert result.consent_authenticated is False
    assert result.trusted_clock_verified is False
    assert result.external_action_authorized is False
    assert writer.events(scope) == prior_events
    assert writer.get(side.memory_id, other_scope) == side
    assert writer.get(original.memory_id, scope, include_expired=True).revision == (
        2 if matching_target_update else 1
    )
