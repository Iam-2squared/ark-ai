"""Registry policy and atomic audit are separate, inert safety boundaries.

A registry-bound WRITE digest can be made without authenticated approval.
Neither successful local permission preview nor atomic intent/audit storage
grants backend dispatch or proves a real-world exactly-once effect.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PermissionDenied,
    ToolCall,
)
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("never dispatch from disconnected evidence")


def _registry(effect: Effect, backend: NeverExecute, version: str) -> ToolRegistry:
    return ToolRegistry((
        ToolRegistration("fixture.atomic", "fixture.capability", effect, version, backend),
    ))


def _call() -> ToolCall:
    return ToolCall("fixture.atomic", "fixture.capability", "scope:private", {"x": 2})


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_policy_and_atomic_digest_cannot_escalate_to_real_dispatch(tmp_path, effect):
    backend = NeverExecute()
    registry = _registry(effect, backend, "local-backend-v1")
    call = _call()
    gate = PermissionGate()
    grants = (CapabilityGrant(call.capability, call.scope, 2_000),)
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "intent-only.sqlite3")

    if effect is Effect.READ:
        inspected = gate.authorize_registered(registry, call, grants, now_ms=1_000)
        assert inspected.registration.effect is Effect.READ
        # A READ cannot be disguised as the WRITE required by atomic intent.
        with pytest.raises(AtomicPreactionRejected):
            derive_registered_atomic_intent(
                registry, call, occurrence_id="occ_" + "a" * 64,
            )
        assert ledger.inspect(genesis_atomic_preaction_witness()).occurrence_ids == ()
    else:
        # A valid capability grant alone never approves a registered WRITE.
        with pytest.raises(PermissionDenied):
            gate.authorize_registered(registry, call, grants, now_ms=1_000)
        # Deriving a WRITE claim is only identity bookkeeping; it does not
        # require or confer a signed one-shot authorization.
        claim = derive_registered_atomic_intent(
            registry, call, occurrence_id="occ_" + "a" * 64,
        )
        tip = ledger.reserve(claim, retained=genesis_atomic_preaction_witness())
        cold = DisconnectedAtomicPreactionLedger(tmp_path / "intent-only.sqlite3")
        snapshot = cold.inspect(tip)
        assert snapshot.occurrence_ids == (claim.occurrence_id,)
        assert snapshot.tool_dispatch_authorized is False
        assert snapshot.automatic_replay_authorized is False
        assert snapshot.external_effect_proven is False
        assert snapshot.trusted_approval_verified is False
        with pytest.raises(AtomicPreactionRejected):
            cold.reserve(claim, retained=genesis_atomic_preaction_witness())
    assert backend.calls == 0


@pytest.mark.parametrize("changed_effect", (Effect.READ, Effect.WRITE))
def test_registry_revision_change_cannot_relabel_retained_preaction(
    tmp_path, changed_effect,
):
    backend = NeverExecute()
    call = _call()
    initial = _registry(Effect.WRITE, backend, "backend-v1")
    changed = _registry(changed_effect, backend, "backend-v2")
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "rebind.sqlite3")
    original = derive_registered_atomic_intent(
        initial, call, occurrence_id="occ_" + "c" * 64,
    )
    tail = ledger.reserve(original, retained=genesis_atomic_preaction_witness())
    assert original.bound_action_id == initial.bind(call).bound_action_id
    assert initial.revision != changed.revision
    assert initial.bind(call).bound_action_id != changed.bind(call).bound_action_id

    if changed_effect is Effect.READ:
        with pytest.raises(AtomicPreactionRejected):
            derive_registered_atomic_intent(
                changed, call, occurrence_id=original.occurrence_id,
            )
    else:
        rebinding = derive_registered_atomic_intent(
            changed, call, occurrence_id=original.occurrence_id,
        )
        assert rebinding.bound_action_id != original.bound_action_id
        # Even with a fresh retained tip, the same occurrence may not be
        # rewritten under a different registered backend identity.
        with pytest.raises(AtomicPreactionRejected):
            DisconnectedAtomicPreactionLedger(
                tmp_path / "rebind.sqlite3",
            ).reserve(rebinding, retained=tail)
    assert ledger.inspect(tail).occurrence_ids == (original.occurrence_id,)
    assert backend.calls == 0
