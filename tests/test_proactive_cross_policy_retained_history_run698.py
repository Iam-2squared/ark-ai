"""Cross-policy synthetic proactive history and custody failure isolation.

A local receipt never permits notifications, dispatch, or replay. Even when
policy throttles are independent, corruption in any retained SQLite row must
block the shared ledger rather than silently skip a different policy's row.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.proactive_synthetic_continuity_review import (
    read_proactive_witness,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64


def policy(owner):
    return SyntheticTriggerPolicy(
        owner, "local", "scheduled-check", 1, "v1", 10, 100, 2,
    )


def prepare(store, active, *, observation, at):
    receipt = store.prepare(
        active, source_digest=A, observation_digest=observation,
        observed_at_ms=at, now_ms=at,
    )
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    return receipt


def test_two_policy_admissions_recover_with_independent_rate_limits(tmp_path):
    path = tmp_path / "synthetic.sqlite"
    initial = SyntheticProactiveLedger(path)
    alice, bob = policy("alice"), policy("bob")
    first = prepare(initial, alice, observation=B, at=100)
    second = prepare(initial, bob, observation=B, at=100)
    previous = read_proactive_witness(initial)

    cold = SyntheticProactiveLedger(path)
    assert read_proactive_witness(cold, retained=previous) == previous
    with pytest.raises(SyntheticTriggerRejected, match="minimum preparation interval"):
        cold.prepare(
            alice, source_digest=A, observation_digest=C,
            observed_at_ms=109, now_ms=109, retained=previous,
        )
    assert cold.count() == 2

    new_bob = prepare(cold, bob, observation=C, at=110)
    updated = read_proactive_witness(cold, retained=previous)
    new_alice = prepare(cold, alice, observation=D, at=110)
    final = read_proactive_witness(
        SyntheticProactiveLedger(path), retained=updated,
    )
    assert len({first.trigger_id, second.trigger_id,
                new_bob.trigger_id, new_alice.trigger_id}) == 4
    assert len(final.row_hashes) == 4
    assert len(previous.row_hashes) == 2
    assert SyntheticProactiveLedger(path).count() == 4


@pytest.mark.parametrize(
    ("column", "tampered"),
    (
        ("source_digest", "not-a-hash"),
        ("observation_digest", "bad"),
        ("scope_digest", "bad"),
        ("trigger_id", "trigger_" + "0" * 64),
    ),
)
def test_corrupt_other_policy_row_blocks_shared_ledger_not_only_its_owner(
    tmp_path, column, tampered,
):
    path = tmp_path / "corrupted.sqlite"
    ledger = SyntheticProactiveLedger(path)
    alice, bob = policy("alice"), policy("bob")
    first = prepare(ledger, alice, observation=B, at=100)
    prepare(ledger, bob, observation=B, at=100)
    with sqlite3.connect(path) as connection:
        connection.execute(
            f"UPDATE synthetic_prepared_triggers SET {column}=? "
            "WHERE trigger_id=?",
            (tampered, first.trigger_id),
        )

    cold = SyntheticProactiveLedger if False else ledger
    with pytest.raises(SyntheticTriggerRejected):
        cold.prepare(
            bob, source_digest=A, observation_digest=C,
            observed_at_ms=110, now_ms=110,
        )
    with pytest.raises(SyntheticTriggerRejected):
        cold.count()
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_prepared_triggers"
        ).fetchone()[0] == 2


@pytest.mark.parametrize("lost_owner", ("alice", "bob"))
def test_retained_two_policy_history_rejects_deleted_other_row(
    tmp_path, lost_owner,
):
    path = tmp_path / "missing-history.sqlite"
    ledger = SyntheticProactiveLedger(path)
    alice, bob = policy("alice"), policy("bob")
    first = prepare(ledger, alice, observation=B, at=100)
    second = prepare(ledger, bob, observation=B, at=100)
    retained = read_proactive_witness(ledger)
    lost = first.trigger_id if lost_owner == "alice" else second.trigger_id

    with sqlite3.connect(path) as connection:
        connection.execute(
            "DELETE FROM synthetic_prepared_triggers WHERE trigger_id=?",
            (lost,),
        )
    with pytest.raises(SyntheticTriggerRejected, match="history changed"):
        read_proactive_witness(ledger, retained=retained)
    assert retained.row_hashes
