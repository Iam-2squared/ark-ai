"""Two local gates cannot create two durable synthetic WRITE reservations.

This is an inert race across independent SQLite handles, not trusted consent,
a real backend dispatch, external exactly-once execution or a clock proof.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from test_registry_policy_durable_occurrence_restart_run643 import _fixture

from ark.agency.contracts import OneShotAuthorization
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.policy import PermissionGate


@pytest.mark.parametrize(
    "conflict", ("same_token", "same_occurrence"),
)
def test_fresh_gates_race_for_one_durable_reservation(
    tmp_path, conflict,
):
    registry, call, grant, token, _, occurrence, path, backend = _fixture(tmp_path)
    alternatives = (
        token if conflict == "same_token"
        else OneShotAuthorization("different-local-token", call.request_id, 200)
    )
    occurrences = (
        ("occ_" + "a" * 64, "occ_" + "b" * 64)
        if conflict == "same_token" else (occurrence, occurrence)
    )
    barrier = Barrier(2)

    def contender(args):
        candidate_token, candidate_occurrence = args
        local_gate = PermissionGate()
        bound = local_gate.authorize_registered(
            registry, call, (grant,), now_ms=100, one_shot=candidate_token,
        )
        assert bound.call is call
        barrier.wait(timeout=15)
        try:
            receipt = SyntheticOccurrenceStore(path).reserve_synthetic(
                registry, call, candidate_token,
                occurrence_id=candidate_occurrence, now_ms=100,
            )
            return ("reserved", receipt)
        except SyntheticReplayRejected as exc:
            return ("rejected", str(exc))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(contender, (
            (token, occurrences[0]),
            (alternatives, occurrences[1]),
        )))
    assert sorted(state for state, _ in results) == ["rejected", "reserved"]
    assert "already reserved" in next(
        detail for state, detail in results if state == "rejected"
    )
    receipt = next(detail for state, detail in results if state == "reserved")
    assert receipt.dispatch_authorized is False
    assert receipt.outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
    assert backend.calls == 0


def test_new_gate_cannot_override_persisted_clock_lower_bound(tmp_path):
    registry, call, grant, token, ledger, occurrence, path, backend = _fixture(tmp_path)
    PermissionGate().authorize_registered(
        registry, call, (grant,), now_ms=100, one_shot=token,
    )
    ledger.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence, now_ms=100,
    )
    later_token = OneShotAuthorization("different-token-clock", call.request_id, 200)
    PermissionGate().authorize_registered(
        registry, call, (grant,), now_ms=99, one_shot=later_token,
    )
    with pytest.raises(SyntheticReplayRejected, match="clock regressed"):
        SyntheticOccurrenceStore(path).reserve_synthetic(
            registry, call, later_token,
            occurrence_id="occ_" + "c" * 64, now_ms=99,
        )
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
    assert backend.calls == 0
