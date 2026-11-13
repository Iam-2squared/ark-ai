"""Manual-only post-COMMIT Memory triage requires global event continuity.

All mutations below are deliberately confined to disposable SQLite fixtures;
nothing authorizes replay, deletion, promotion, or real-world execution.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import postcommit_uncertainty_review as triage
from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "manual-uncertain.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("owner-a", "private")
    store.put(MemoryWrite(scope, "stable", "original"), expected_revision=0)
    retained = observe_memory_generation_for_cas(store, scope, "stable")
    proposed = MemoryWrite(scope, "stable", "updated")
    return store, retained, proposed


@pytest.mark.parametrize(
    "damage", (
        "remove_unrelated_event", "delete_sequence",
        "duplicate_sequence", "regress_sequence",
    ),
)
def test_unrelated_or_global_log_damage_precludes_manual_classification(
    tmp_path, damage: str,
) -> None:
    store, retained, proposed = _case(tmp_path)
    other = store.put(
        MemoryWrite(MemoryScope("owner-b", "private"), "other", "synthetic"),
        expected_revision=0,
    )
    with sqlite3.connect(store.path) as conn:
        if damage == "remove_unrelated_event":
            conn.execute(
                "DELETE FROM memory_events WHERE memory_id=?", (other.memory_id,),
            )
        elif damage == "delete_sequence":
            conn.execute("DELETE FROM sqlite_sequence WHERE name='memory_events'")
        elif damage == "duplicate_sequence":
            conn.execute(
                "INSERT INTO sqlite_sequence(name,seq) VALUES('memory_events',2)"
            )
        else:
            conn.execute(
                "UPDATE sqlite_sequence SET seq=0 WHERE name='memory_events'"
            )
    with pytest.raises(triage.MemoryCommitTriageRejected, match="manual review"):
        triage.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )


def test_global_history_checker_is_required_before_private_sqlite(
    tmp_path, monkeypatch,
) -> None:
    store, retained, proposed = _case(tmp_path)
    calls = []

    def forged_checker(_):
        calls.append(True)

    monkeypatch.setattr(
        triage, "_check_global_memory_event_highwater", forged_checker,
    )
    with pytest.raises(
        triage.MemoryCommitTriageRejected, match="input or denial changed",
    ):
        triage.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )
    assert calls == []


def test_intact_global_log_still_returns_denial_only_manual_review(tmp_path) -> None:
    store, retained, proposed = _case(tmp_path)
    report = triage.review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert report.disposition == "LOCAL_UNCHANGED"
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.caller_attribution_proven is False
    assert report.trusted_clock_proven is False
