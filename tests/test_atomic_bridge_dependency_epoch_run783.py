"""Disconnected registered atomic claims retain their original hash and grammar.

Only synthetic local registry identities are used. No ToolBackend is executed,
and an inert claim is never treated as approval or trusted custody.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_atomic_registry_bridge as bridge
from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import AtomicPreactionRejected
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("inert claim must not dispatch")


def _fixture() -> tuple[ToolRegistry, ToolCall, NeverExecute]:
    backend = NeverExecute()
    call = ToolCall("fixture.write", "fixture.write", "offline:fixture", {"v": 1})
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write", "fixture.write", Effect.WRITE, "local:mock", backend,
        ),
    ))
    return registry, call, backend


@pytest.mark.parametrize(
    "dependency", ("sha256", "occurrence_grammar", "bound_grammar", "request_grammar"),
)
def test_preinstalled_bridge_substitution_refused_before_bind(
    monkeypatch: pytest.MonkeyPatch, dependency: str,
) -> None:
    registry, call, backend = _fixture()
    invoked: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append(dependency)
        raise AssertionError("substituted bridge dependency invoked")

    class ForgedGrammar:
        def fullmatch(self, _value: object) -> object:
            return forbidden()

    with monkeypatch.context() as patch:
        if dependency == "sha256":
            patch.setattr(bridge.hashlib, "sha256", forbidden)
        else:
            attr = {
                "occurrence_grammar": "_OCC",
                "bound_grammar": "_BOUND",
                "request_grammar": "_REQUEST",
            }[dependency]
            patch.setattr(bridge, attr, ForgedGrammar())
        with pytest.raises(
            AtomicPreactionRejected, match="registry intent digest or grammar changed",
        ):
            bridge.derive_registered_atomic_intent(
                registry, call, occurrence_id="occ_" + "a" * 64,
            )
    assert invoked == []
    assert backend.calls == 0


def test_bind_callback_cannot_swap_sha_before_request_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, call, backend = _fixture()
    original_bind = registry.bind
    invoked: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append("sha256")
        raise AssertionError("forged digest must not see request identifier")

    with monkeypatch.context() as patch:
        def bind_then_swap(value: ToolCall):
            result = original_bind(value)
            patch.setattr(bridge.hashlib, "sha256", forbidden)
            return result

        patch.setattr(registry, "bind", bind_then_swap)
        # A nested fail-closed refusal may be normalized by the bridge's
        # original ValueError boundary; neither path may run the forged hash.
        with pytest.raises(
            AtomicPreactionRejected,
            match="registry intent digest or grammar changed|registered intent binding refused",
        ):
            bridge.derive_registered_atomic_intent(
                registry, call, occurrence_id="occ_" + "b" * 64,
            )
    assert invoked == []
    assert backend.calls == 0


def test_original_registry_intent_stays_deterministic_and_inert() -> None:
    registry, call, backend = _fixture()
    a = bridge.derive_registered_atomic_intent(
        registry, call, occurrence_id="occ_" + "c" * 64,
    )
    b = bridge.derive_registered_atomic_intent(
        registry, call, occurrence_id="occ_" + "c" * 64,
    )
    assert a == b
    assert a.bound_action_id == registry.bind(call).bound_action_id
    assert a.request_sha256 != call.arguments_sha256
    assert backend.calls == 0
