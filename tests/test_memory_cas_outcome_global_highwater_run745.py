"""Unrelated event gaps must block manual-only Memory CAS outcome classification.

Disposable SQLite fixtures; this never attempts a retry, purge, or real tool.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_cas_outcome_review as outcome
from ark.memory import generation_fenced_cas as cas


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "outcome-global-history.sqlite3", clock_ms=lambda: 100,
    )
    scope = MemoryScope("owner", "private")
    store.put(MemoryWrite(scope, "stable", "first"), expected_revision=0)
    retained = cas.observe_memory_generation_for_cas(store, scope, "stable")
    foreign = MemoryScope("different-owner", "journal")
    store.put(MemoryWrite(foreign, "foreign-1", "synthetic"), expected_revision=0)
    store.put(MemoryWrite(foreign, "foreign-2", "synthetic"), expected_revision=0)
    proposed = MemoryWrite(scope, "stable", "second")
    return store, retained, proposed


def _inspect(store, retained, proposed):
    return outcome.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )


def test_other_scopes_do_not_block_healthy_manual_only_observation(tmp_path):
    store, retained, proposed = _case(tmp_path)
    unchanged = _inspect(store, retained, proposed)
    assert unchanged.observation == "UNCHANGED_OBSERVED"
    assert unchanged.automatic_retry_authorized is False
    assert unchanged.commit_attributed_to_caller is False
    store.put(proposed, expected_revision=1)
    updated = _inspect(store, retained, proposed)
    assert updated.observation == "ONE_MATCHING_UPDATE_OBSERVED"
    assert updated.commit_attributed_to_caller is False
    assert updated.external_action_authorized is False


@pytest.mark.parametrize("tamper", (
    "remove_foreign_middle",
    "remove_foreign_tail",
    "advance_sequence",
    "rewind_sequence",
    "drop_sequence",
    "duplicate_sequence",
))
def test_global_event_or_sequence_gap_refuses_row_local_cas_observation(
    tmp_path, tamper,
):
    store, retained, proposed = _case(tmp_path)
    assert _inspect(store, retained, proposed).observation == "UNCHANGED_OBSERVED"
    with sqlite3.connect(store.path) as conn:
        if tamper == "remove_foreign_middle":
            conn.execute("DELETE FROM memory_events WHERE event_id=2")
        elif tamper == "remove_foreign_tail":
            conn.execute("DELETE FROM memory_events WHERE event_id=3")
        elif tamper == "advance_sequence":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=50 WHERE name='memory_events'"
            )
        elif tamper == "rewind_sequence":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=2 WHERE name='memory_events'"
            )
        elif tamper == "drop_sequence":
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name='memory_events'"
            )
        else:
            conn.execute(
                "INSERT INTO sqlite_sequence(name,seq) VALUES('memory_events',3)"
            )
    # These edits leave the target's own prefix and row unchanged. Their
    # unrelated loss must still quarantine ambiguous commit attribution.
    with pytest.raises(outcome.MemoryCASOutcomeRejected):
        _inspect(store, retained, proposed)


def test_review_is_read_only_and_does_not_claim_historical_authorship(tmp_path):
    store, retained, proposed = _case(tmp_path)
    with sqlite3.connect(store.path) as conn:
        before = conn.execute(
            "SELECT event_id,memory_id,operation,revision FROM memory_events "
            "ORDER BY event_id"
        ).fetchall()
    receipt = _inspect(store, retained, proposed)
    with sqlite3.connect(store.path) as conn:
        after = conn.execute(
            "SELECT event_id,memory_id,operation,revision FROM memory_events "
            "ORDER BY event_id"
        ).fetchall()
    assert before == after
    assert receipt.commit_attributed_to_caller is False
    assert receipt.automatic_retry_authorized is False
