"""Registry-bound synthetic pre-action claims never authorize tool dispatch."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("no mock backend dispatch is allowed")


def _registered(effect: Effect) -> tuple[ToolRegistry, ToolCall, NeverExecute]:
    backend = NeverExecute()
    call = ToolCall("writer", "fixture.write", "offline", {"k": "v"})
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", effect, "local", backend),
    ))
    return registry, call, backend


def test_binding_to_real_registry_write_remains_inert(tmp_path: Path) -> None:
    registry, call, backend = _registered(Effect.WRITE)
    claim = derive_registered_atomic_intent(
        registry, call, occurrence_id="occ_" + "a" * 64,
    )
    bound = registry.bind(call)
    assert claim.bound_action_id == bound.bound_action_id
    assert claim.request_sha256 != call.arguments_sha256
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    tip = store.reserve(claim, retained=genesis_atomic_preaction_witness())
    assert store.inspect(tip).tool_dispatch_authorized is False
    assert store.inspect(tip).automatic_replay_authorized is False
    assert backend.calls == 0


@pytest.mark.parametrize("effect", [Effect.READ])
def test_registered_read_is_not_reclassified_as_write(effect: Effect) -> None:
    registry, call, backend = _registered(effect)
    with pytest.raises(AtomicPreactionRejected):
        derive_registered_atomic_intent(
            registry, call, occurrence_id="occ_" + "a" * 64,
        )
    assert backend.calls == 0


@pytest.mark.parametrize("identity", [
    "occ_" + "x" * 64, "bad", "occ_" + "a" * 63,
])
def test_noncanonical_occurrence_rejected_before_registry_bind(
    identity: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, call, backend = _registered(Effect.WRITE)
    def forbidden(_call: ToolCall) -> object:
        raise AssertionError("must reject before registry lookup")
    monkeypatch.setattr(registry, "bind", forbidden)
    with pytest.raises(AtomicPreactionRejected):
        derive_registered_atomic_intent(registry, call, occurrence_id=identity)
    assert backend.calls == 0


def test_patched_registry_bind_is_rejected_without_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, call, backend = _registered(Effect.WRITE)
    def forged(_self: ToolRegistry, _call: ToolCall) -> object:
        raise AssertionError("forged registry method invoked")
    monkeypatch.setattr(ToolRegistry, "bind", forged)
    with pytest.raises(AtomicPreactionRejected):
        derive_registered_atomic_intent(
            registry, call, occurrence_id="occ_" + "a" * 64,
        )
    assert backend.calls == 0
