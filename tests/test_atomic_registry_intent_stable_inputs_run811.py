"""Registry-derived inert WRITE claims cannot cross an altered identity boundary."""

from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
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
        raise AssertionError("registry identity test must not execute a tool")


def _fixture() -> tuple[ToolRegistry, ToolCall, NeverExecute]:
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local:fixture", backend),
    ))
    call = ToolCall("writer", "fixture.write", "local:fixture", {"record": 1})
    return registry, call, backend


def test_registered_intent_stays_identical_and_nonexecuting() -> None:
    registry, call, backend = _fixture()
    first = derive_registered_atomic_intent(
        registry, call, occurrence_id="occ_" + "a" * 64,
    )
    second = derive_registered_atomic_intent(
        registry, call, occurrence_id="occ_" + "a" * 64,
    )
    assert type(first) is AtomicIntentClaim
    assert first == second
    assert first.bound_action_id == registry.bind(call).bound_action_id
    assert first.request_sha256 != call.arguments_sha256
    assert backend.calls == 0


@pytest.mark.parametrize(
    "target",
    ("instance-bind", "claim-init", "claim-field", "call-tool", "call-request-id"),
)
def test_preinstalled_mutable_identity_seams_fail_closed_without_callbacks(
    monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    registry, call, backend = _fixture()
    invoked: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append(target)
        raise AssertionError("substituted identity code must never execute")

    with monkeypatch.context() as patch:
        if target == "instance-bind":
            patch.setattr(registry, "bind", forbidden)
        elif target == "claim-init":
            patch.setattr(AtomicIntentClaim, "__init__", forbidden)
        elif target == "claim-field":
            patch.setattr(AtomicIntentClaim, "request_sha256", property(forbidden))
        elif target == "call-tool":
            patch.setattr(ToolCall, "tool", property(forbidden))
        else:
            patch.setattr(ToolCall, "request_id", property(forbidden))
        with pytest.raises((AtomicPreactionRejected, ValueError)):
            derive_registered_atomic_intent(
                registry, call, occurrence_id="occ_" + "b" * 64,
            )
    assert invoked == []
    assert backend.calls == 0


@pytest.mark.parametrize("identity", ["occ_" + "f" * 64, "occ_" + "0" * 64])
def test_distinct_synthetic_occurrence_is_bound_to_distinct_claim(
    identity: str,
) -> None:
    registry, call, backend = _fixture()
    claim = derive_registered_atomic_intent(registry, call, occurrence_id=identity)
    assert claim.occurrence_id == identity
    assert backend.calls == 0
