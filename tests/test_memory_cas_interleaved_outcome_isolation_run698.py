"""Interleaved WAL rows never attribute an uncertain generation-CAS writer.

All events and clocks are synthetic, and all databases are disposable. Foreign
scope activity must not create an artificial same-row CAS conflict, while an
identical update by a different local handle is still not caller attribution.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryConflictError
from ark.memory.generation_cas_outcome_review import (
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("other_owner", "other_namespace"),
    (("owner-a", "other"), ("owner-b", "private"), ("owner-b", "other")),
)
def test_unrelated_wal_appends_leave_original_cas_review_unchanged(
    tmp_path, other_owner, other_namespace,
):
    path = tmp_path / "interleaved.sqlite"
    tick = [100]
    target_scope = MemoryScope("owner-a", "private")
    other_scope = MemoryScope(other_owner, other_namespace)
    first = SQLiteMemoryStore(path, clock_ms=lambda: tick[0])
    original = first.put(MemoryWrite(target_scope, "target", "before"))
    retained = observe_memory_generation_for_cas(first, target_scope, "target")

    tick[0] = 200
    foreign = SQLiteMemoryStore(path, clock_ms=lambda: tick[0])
    foreign.put(MemoryWrite(other_scope, "first", "foreign-1"))
    foreign.put(MemoryWrite(other_scope, "second", "foreign-2"))

    proposed = MemoryWrite(target_scope, "target", "after")
    report = review_memory_generation_cas_outcome(first, proposed, retained=retained)
    assert report.observation == "UNCHANGED_OBSERVED"
    assert report.commit_attributed_to_caller is False
    assert report.automatic_retry_authorized is False
    assert report.external_action_authorized is False

    tick[0] = 300
    advanced = generation_fenced_memory_update(
        first, proposed, retained=retained,
    )
    assert advanced.memory_id == original.memory_id
    assert advanced.revision == 2
    cold = SQLiteMemoryStore(path, clock_ms=lambda: tick[0])
    assert cold.get(original.memory_id, target_scope).content == "after"
    assert len(tuple(cold.events(other_scope))) == 2
    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(
            first, MemoryWrite(target_scope, "target", "replay"),
            retained=retained,
        )


@pytest.mark.parametrize(
    ("foreign_payload", "classification"),
    (
        ("proposed", "ONE_MATCHING_UPDATE_OBSERVED"),
        ("different", "DIVERGED_OBSERVED"),
    ),
)
@pytest.mark.parametrize("other_owner", ("owner-a", "owner-b"))
def test_foreign_matching_update_with_unrelated_events_is_never_attributed(
    tmp_path, foreign_payload, classification, other_owner,
):
    path = tmp_path / "uncertain.sqlite"
    tick = [100]
    scope = MemoryScope("owner-a", "private")
    other_scope = MemoryScope(other_owner, "other")
    observer = SQLiteMemoryStore(path, clock_ms=lambda: tick[0])
    original = observer.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(observer, scope, "source")
    proposed = MemoryWrite(scope, "source", "proposed", {"tag": "new"})

    tick[0] = 200
    competitor = SQLiteMemoryStore(path, clock_ms=lambda: tick[0])
    written = generation_fenced_memory_update(
        competitor,
        MemoryWrite(scope, "source", foreign_payload, {"tag": "new"}),
        retained=retained,
    )
    assert written.revision == 2

    tick[0] = 300
    competitor.put(MemoryWrite(other_scope, "unrelated", "fixture"))
    report = review_memory_generation_cas_outcome(
        observer, proposed, retained=retained,
    )
    assert report.observation == classification
    assert report.commit_attributed_to_caller is False
    assert report.automatic_retry_authorized is False
    assert report.consent_authenticated is False
    assert report.trusted_clock_verified is False
    assert report.external_action_authorized is False
    assert SQLiteMemoryStore(path, clock_ms=lambda: tick[0]).get(
        original.memory_id, scope,
    ).content == foreign_payload
    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(observer, proposed, retained=retained)
