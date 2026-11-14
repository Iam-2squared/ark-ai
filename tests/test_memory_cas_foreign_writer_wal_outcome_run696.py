"""Two SQLite handles cannot attribute a matching COMMIT-UNKNOWN update.

A second local writer may persist exactly the proposed bytes while the first
client is uncertain. WAL snapshots and locally matching hashes never identify
which caller committed and never authorize an automatic retry.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

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
    ("foreign_content", "foreign_metadata", "foreign_expiry", "expected"),
    (
        ("proposed", {"label": "same"}, 900, "ONE_MATCHING_UPDATE_OBSERVED"),
        ("different", {"label": "same"}, 900, "DIVERGED_OBSERVED"),
        ("proposed", {"label": "other"}, 900, "DIVERGED_OBSERVED"),
        ("proposed", {"label": "same"}, 800, "DIVERGED_OBSERVED"),
    ),
)
def test_independent_wal_writer_never_authenticates_ambiguous_cas(
    tmp_path, foreign_content, foreign_metadata, foreign_expiry, expected,
):
    path = tmp_path / "memory.sqlite"
    clock = [100]
    scope = MemoryScope("local-owner", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    original = first.put(
        MemoryWrite(scope, "fixture", "before", expires_at_ms=1000),
    )
    retained = observe_memory_generation_for_cas(first, scope, "fixture")

    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"

    second = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    proposed = MemoryWrite(
        scope, "fixture", "proposed", {"label": "same"}, expires_at_ms=900,
    )
    clock[0] = 200
    foreign = generation_fenced_memory_update(
        second,
        MemoryWrite(
            scope, "fixture", foreign_content, foreign_metadata,
            expires_at_ms=foreign_expiry,
        ),
        retained=retained,
    )
    assert foreign.memory_id == original.memory_id
    assert foreign.revision == 2

    # The first handle's old token was obtained before the other writer ran.
    # This is manual-only review, even when *all* proposed bytes match.
    reviewed = review_memory_generation_cas_outcome(
        first, proposed, retained=retained,
    )
    assert reviewed.observation == expected
    assert reviewed.commit_attributed_to_caller is False
    assert reviewed.automatic_retry_authorized is False
    assert reviewed.consent_authenticated is False
    assert reviewed.trusted_clock_verified is False
    assert reviewed.external_action_authorized is False

    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(first, proposed, retained=retained)

    restarted = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    assert restarted.get(original.memory_id, scope).revision == 2
    assert len(restarted.events(scope)) == 2
    latest = observe_memory_generation_for_cas(restarted, scope, "fixture")
    assert latest.create_event_id == retained.create_event_id
    assert latest.last_event_id > retained.last_event_id
    assert latest.event_prefix_sha256 != retained.event_prefix_sha256
    assert latest.external_action_authorized is False
