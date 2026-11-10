"""Read-only local recovery quarantine cannot silently authorize a WRITE."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionSnapshot,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_recovery_quarantine import (
    AtomicRecoveryQuarantineRejected,
    review_registered_atomic_recovery,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.registry import ToolRegistration, ToolRegistry

_OCC = "occ_" + "a" * 64


class NeverExecute:
    calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("synthetic recovery must not dispatch")


def _registry(effect: Effect = Effect.WRITE, name: str = "writer"):
    backend = NeverExecute()
    call = ToolCall(name, "fixture.write", "offline", {"k": "v"})
    registry = ToolRegistry((
        ToolRegistration(name, "fixture.write", effect, "local", backend),
    ))
    return registry, call, backend


def _review(store, retained, registry, call, occurrence=_OCC):
    return review_registered_atomic_recovery(
        store, retained, registry, call, occurrence_id=occurrence,
    )


@pytest.mark.parametrize("present", [False, True])
def test_local_membership_always_requires_manual_review(
    tmp_path: Path, present: bool,
) -> None:
    registry, call, backend = _registry()
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    witness = genesis_atomic_preaction_witness()
    if present:
        claim = derive_registered_atomic_intent(
            registry, call, occurrence_id=_OCC,
        )
        witness = store.reserve(claim, retained=witness)
    outcome = _review(store, witness, registry, call)
    assert outcome.occurrence_id == _OCC
    assert outcome.locally_recorded is present
    assert outcome.retained_count == int(present)
    assert outcome.manual_review_required is True
    for name in (
        "binding_proven", "tool_dispatch_authorized",
        "automatic_replay_authorized", "external_effect_proven",
        "independent_custody_proven",
    ):
        assert getattr(outcome, name) is False
    assert backend.calls == 0
    assert not hasattr(outcome, "execute")


def test_stale_witness_never_falls_back_to_best_effort(
    tmp_path: Path,
) -> None:
    registry, call, backend = _registry()
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    genesis = genesis_atomic_preaction_witness()
    claim = derive_registered_atomic_intent(
        registry, call, occurrence_id=_OCC,
    )
    store.reserve(claim, retained=genesis)
    with pytest.raises(AtomicRecoveryQuarantineRejected):
        _review(store, genesis, registry, call)
    assert backend.calls == 0


def test_same_occurrence_with_unrelated_registration_is_not_binding_proof(
    tmp_path: Path,
) -> None:
    first_registry, first_call, first_backend = _registry()
    second_registry, second_call, second_backend = _registry(name="other")
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    claim = derive_registered_atomic_intent(
        first_registry, first_call, occurrence_id=_OCC,
    )
    tip = store.reserve(claim, retained=genesis_atomic_preaction_witness())
    outcome = _review(store, tip, second_registry, second_call)
    # A local occurrence match is not a match of registered action/request.
    assert outcome.locally_recorded is True
    assert outcome.binding_proven is False
    assert outcome.tool_dispatch_authorized is False
    assert outcome.manual_review_required is True
    assert first_backend.calls == second_backend.calls == 0


def test_read_registration_cannot_become_write_on_recovery(
    tmp_path: Path,
) -> None:
    registry, call, backend = _registry(Effect.READ)
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    with pytest.raises(AtomicRecoveryQuarantineRejected):
        _review(store, genesis_atomic_preaction_witness(), registry, call)
    assert backend.calls == 0


@pytest.mark.parametrize("occurrence", ["bad", "occ_" + "f" * 63])
def test_invalid_occurrence_rejected_without_dispatch(
    tmp_path: Path, occurrence: str,
) -> None:
    registry, call, backend = _registry()
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    with pytest.raises(AtomicRecoveryQuarantineRejected):
        _review(
            store, genesis_atomic_preaction_witness(),
            registry, call, occurrence,
        )
    assert backend.calls == 0


def test_rebound_snapshot_authority_cannot_run_before_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, call, backend = _registry()
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    called = []

    def forbidden(_self: object) -> bool:
        called.append(True)
        raise AssertionError("substituted authority getter ran")

    monkeypatch.setattr(
        AtomicPreactionSnapshot,
        "tool_dispatch_authorized",
        property(forbidden),
    )
    with pytest.raises(
        AtomicRecoveryQuarantineRejected, match="authority definition changed",
    ):
        _review(store, genesis_atomic_preaction_witness(), registry, call)
    assert called == []
    assert backend.calls == 0
