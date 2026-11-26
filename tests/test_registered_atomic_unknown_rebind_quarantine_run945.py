"""Registered WRITE identity drift cannot rewrite an ambiguous local intent.

These disconnected reviews have no authenticated consent, trusted clock,
live tool backend, exactly-once execution, or authority to retry a WRITE.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, PermissionDenied, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.disconnected_atomic_unknown_outcome_review import (
    AtomicUnknownOutcomeRejected,
    review_atomic_unknown_outcome,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _ForbiddenBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("disconnected review may not dispatch")


def _registry(version: str, backend: _ForbiddenBackend) -> ToolRegistry:
    return ToolRegistry((
        ToolRegistration(
            "fixture.atomic", "fixture.write", Effect.WRITE, version, backend,
        ),
    ))


@pytest.mark.parametrize("change", ("backend-version", "scope", "arguments"))
def test_cold_unknown_occurrence_refuses_registry_and_request_rebinding(
    tmp_path, change: str,
) -> None:
    path = tmp_path / "synthetic-bound-unknown.sqlite3"
    backend = _ForbiddenBackend()
    first_registry = _registry("offline-v1", backend)
    original_call = ToolCall(
        "fixture.atomic", "fixture.write", "synthetic-private", {"value": 1},
    )
    occurrence_id = "occ_" + "a" * 64
    old = derive_registered_atomic_intent(
        first_registry, original_call, occurrence_id=occurrence_id,
    )
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    genesis = genesis_atomic_preaction_witness()
    retained = ledger.reserve(old, retained=genesis)

    changed_registry = (
        _registry("offline-v2", backend)
        if change == "backend-version" else first_registry
    )
    changed_call = (
        ToolCall(
            "fixture.atomic", "fixture.write", "synthetic-other-private",
            {"value": 1},
        )
        if change == "scope" else
        ToolCall(
            "fixture.atomic", "fixture.write", "synthetic-private",
            {"value": 2},
        )
        if change == "arguments" else original_call
    )
    rebound = derive_registered_atomic_intent(
        changed_registry, changed_call, occurrence_id=occurrence_id,
    )
    assert (rebound.bound_action_id, rebound.request_sha256) != (
        old.bound_action_id, old.request_sha256,
    )
    with pytest.raises(AtomicUnknownOutcomeRejected):
        review_atomic_unknown_outcome(
            DisconnectedAtomicPreactionLedger(path), genesis, rebound,
        )

    for witness, expected in ((genesis, "LOCALLY_RECORDED"), (retained, "PREEXISTING")):
        review = review_atomic_unknown_outcome(
            DisconnectedAtomicPreactionLedger(path), witness, old,
        )
        assert review.local_state == expected
        assert review.locally_present is True
        assert review.manual_review_required is True
        assert review.dispatch_authorized is False
        assert review.automatic_replay_authorized is False
        assert review.external_effect_verified is False
    assert backend.calls == 0


def test_valid_grant_does_not_authorize_a_registered_write_during_triage(
    tmp_path,
) -> None:
    backend = _ForbiddenBackend()
    registry = _registry("offline-v1", backend)
    call = ToolCall(
        "fixture.atomic", "fixture.write", "synthetic-private", {"value": 1},
    )
    with pytest.raises(PermissionDenied):
        PermissionGate().authorize_registered(
            registry, call,
            (CapabilityGrant("fixture.write", "synthetic-private", 1_000),),
            now_ms=100,
        )
    ledger = DisconnectedAtomicPreactionLedger.create(
        tmp_path / "synthetic-permission-denied.sqlite3",
    )
    claim = derive_registered_atomic_intent(
        registry, call, occurrence_id="occ_" + "b" * 64,
    )
    review = review_atomic_unknown_outcome(
        ledger, genesis_atomic_preaction_witness(), claim,
    )
    assert review.local_state == "UNCHANGED"
    assert review.locally_present is False
    assert review.manual_review_required is True
    assert review.dispatch_authorized is False
    assert backend.calls == 0
