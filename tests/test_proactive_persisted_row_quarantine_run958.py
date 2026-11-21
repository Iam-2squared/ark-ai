"""Run958: corrupt local proactive marker rows quarantine a cold SQLite store.

All fixtures are synthetic digests; no real notification, capture, dispatch,
user consent, or action is created. A successful preparation is NOT authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy() -> SyntheticTriggerPolicy:
    return SyntheticTriggerPolicy(
        owner="fixture-owner",
        namespace="private",
        definition_id="fixture-definition",
        revision=1,
        policy_revision="fixture-policy",
        minimum_interval_ms=10,
        rolling_window_ms=100,
        max_preparations_per_window=2,
    )


@pytest.mark.parametrize(
    ("column", "corrupted"),
    (
        ("trigger_id", "trigger_" + "f" * 64),
        ("scope_digest", sqlite3.Binary(b"a" * 64)),
        ("policy_digest", "g" * 64),
        ("source_digest", "c" * 64),
        ("observation_digest", "b" * 63),
        ("observed_at_ms", sqlite3.Binary(b"10")),
        ("prepared_at_ms", 9),
    ),
)
def test_cold_proactive_marker_corruption_fails_closed_without_repair(
    tmp_path, column: str, corrupted: object,
) -> None:
    path = tmp_path / "synthetic-proactive-integrity.sqlite"
    active = SyntheticProactiveLedger(path)
    receipt = active.prepare(
        _policy(),
        source_digest="a" * 64,
        observation_digest="b" * 64,
        observed_at_ms=10,
        now_ms=10,
    )
    assert active.count() == 1
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False

    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE synthetic_prepared_triggers SET {column}=?",
            (corrupted,),
        )
        tampered = conn.execute(
            "SELECT * FROM synthetic_prepared_triggers"
        ).fetchall()
        assert len(tampered) == 1

    with pytest.raises(SyntheticTriggerRejected):
        active.count()
    with pytest.raises(SyntheticTriggerRejected):
        SyntheticProactiveLedger(path)
    with pytest.raises(SyntheticTriggerRejected):
        active.prepare(
            _policy(),
            source_digest="d" * 64,
            observation_digest="e" * 64,
            observed_at_ms=20,
            now_ms=20,
        )

    # Failed reads and failed preparations may neither repair nor add rows.
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT * FROM synthetic_prepared_triggers"
        ).fetchall() == tampered
