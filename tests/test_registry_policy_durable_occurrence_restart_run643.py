"""Registry-bound local permission is not durable one-shot authorization.

A new process-local PermissionGate forgets spent tokens. The disconnected
SQLite occurrence ledger must still reject duplicate token or occurrence
claims. No backend method is invoked; nothing is a real consent receipt.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
)
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("the registry must remain disconnected")


def _fixture(tmp_path):
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("fixture.write", "offline.write", Effect.WRITE, "mock-v1", backend),
    ))
    call = ToolCall("fixture.write", "offline.write", "local:private", {"dry_run": True})
    grant = CapabilityGrant("offline.write", "local:private")
    token = OneShotAuthorization("fixture-token", call.request_id, 200)
    path = tmp_path / "durable-local-occurrences.sqlite"
    ledger = SyntheticOccurrenceStore(path)
    occurrence = "occ_" + hashlib.sha256(b"fixture-occurrence").hexdigest()
    return registry, call, grant, token, ledger, occurrence, path, backend


@pytest.mark.parametrize(
    "replay_subject", ("same_token_new_occurrence", "new_token_same_occurrence"),
)
def test_restart_fresh_local_gate_cannot_replay_sqlite_reservation(
    tmp_path, replay_subject,
):
    registry, call, grant, token, ledger, occurrence, path, backend = _fixture(tmp_path)
    gate = PermissionGate()
    original_bound = gate.authorize_registered(
        registry, call, (grant,), now_ms=100, one_shot=token,
    )
    receipt = ledger.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence, now_ms=100,
    )
    assert receipt.dispatch_authorized is False
    assert receipt.outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.bound_action_id == original_bound.bound_action_id

    # This local policy grant can be repeated by a newly constructed gate;
    # it is deliberately not the persistence or authenticity authority.
    restarted_gate = PermissionGate()
    if replay_subject == "same_token_new_occurrence":
        candidate_token = token
        candidate_occurrence = "occ_" + hashlib.sha256(b"different").hexdigest()
    else:
        candidate_token = OneShotAuthorization("another-token", call.request_id, 200)
        candidate_occurrence = occurrence
    restarted_bound = restarted_gate.authorize_registered(
        registry, call, (grant,), now_ms=100, one_shot=candidate_token,
    )
    assert restarted_bound.bound_action_id == original_bound.bound_action_id
    reopened = SyntheticOccurrenceStore(path)
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        reopened.reserve_synthetic(
            registry, call, candidate_token,
            occurrence_id=candidate_occurrence, now_ms=100,
        )
    assert reopened.count_synthetic() == ledger.count_synthetic() == 1
    assert backend.calls == 0


def test_denied_scope_does_not_consume_local_token_or_reserve_occurrence(tmp_path):
    registry, call, grant, token, ledger, occurrence, path, backend = _fixture(tmp_path)
    gate = PermissionGate()
    wrong = CapabilityGrant("offline.write", "local:other")
    with pytest.raises(PermissionDenied, match="no active"):
        gate.authorize_registered(
            registry, call, (wrong,), now_ms=100, one_shot=token,
        )
    assert ledger.count_synthetic() == 0
    gate.authorize_registered(registry, call, (grant,), now_ms=100, one_shot=token)
    ledger.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence, now_ms=100,
    )
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
    assert backend.calls == 0
