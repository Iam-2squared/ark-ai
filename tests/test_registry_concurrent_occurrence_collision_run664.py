"""Simultaneous synthetic WRITE claims use durable SQLite uniqueness.

This is a two-thread/two-connection *mock* race, not an actual tool call,
authenticated approval, trusted clock, or external exactly-once guarantee.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from test_registry_policy_durable_occurrence_restart_run643 import _fixture

from ark.agency.contracts import OneShotAuthorization
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)


@pytest.mark.parametrize(
    "collision",
    ("same_token_distinct_occurrence", "distinct_token_same_occurrence"),
)
def test_two_sqlite_writers_cannot_both_reserve_colliding_identity(
    tmp_path, collision,
):
    registry, call, _grant, token, ledger, occurrence, path, backend = _fixture(
        tmp_path,
    )
    second_token = (
        token if collision == "same_token_distinct_occurrence"
        else OneShotAuthorization("other-concurrent-token", call.request_id, 200)
    )
    second_occurrence = (
        "occ_" + hashlib.sha256(b"other-concurrent-occurrence").hexdigest()
        if collision == "same_token_distinct_occurrence" else occurrence
    )
    # Initialize both *separate* handles before racing. Only reserve_synthetic
    # performs writes once the barrier releases.
    stores = (ledger, SyntheticOccurrenceStore(path))
    ready = Barrier(2)

    def attempt(index):
        ready.wait(timeout=10)
        try:
            receipt = stores[index].reserve_synthetic(
                registry,
                call,
                token if index == 0 else second_token,
                occurrence_id=occurrence if index == 0 else second_occurrence,
                now_ms=100,
            )
        except SyntheticReplayRejected as exc:
            return ("rejected", str(exc))
        assert receipt.dispatch_authorized is False
        assert receipt.outcome_known is False
        assert receipt.automatic_replay_authorized is False
        return ("reserved", receipt.occurrence_id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        a = executor.submit(attempt, 0)
        b = executor.submit(attempt, 1)
        outcomes = (a.result(timeout=30), b.result(timeout=30))
    assert sorted(kind for kind, _ in outcomes) == ["rejected", "reserved"]
    assert "already reserved" in next(value for kind, value in outcomes if kind == "rejected")
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
    assert backend.calls == 0

    # Restarting the fixture ledger cannot manufacture another reservation
    # from the loser; neither the winner nor the loser is execution authority.
    retry = SyntheticOccurrenceStore(path)
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        retry.reserve_synthetic(
            registry, call, token,
            occurrence_id=occurrence, now_ms=100,
        )
    assert retry.count_synthetic() == 1
