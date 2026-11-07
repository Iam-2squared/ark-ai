"""BoundAction result construction must not retarget a registry-bound identity.

These are disconnected registry fixtures; no real backend is executed and no
registration or digest constitutes human approval or an execution grant.
"""

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import BoundAction, ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("registry must never dispatch")


def _fixture():
    backend = _NeverExecute()
    registration = ToolRegistration(
        "offline.write", "fixture.write", Effect.WRITE, "mock-v1", backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("offline.write", "fixture.write", "local", {"n": 1})
    return backend, registration, registry, call


def _clone(value: str) -> str:
    result = ("!" + value)[1:]
    assert result == value and result is not value
    return result


@pytest.mark.parametrize(
    "target",
    (
        "result_revision", "result_call", "result_registration",
        "result_bound_id", "registry_revision",
        "call_scope", "registration_backend_id", "registration_effect",
    ),
)
def test_bound_action_constructor_cannot_retarget_original_registry_epoch(
    monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    backend, registration, registry, call = _fixture()
    original_init = BoundAction.__init__

    def reflected_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if target == "result_revision":
            object.__setattr__(
                self, "registry_revision", _clone(self.registry_revision)
            )
        elif target == "result_call":
            cloned = ToolCall(
                call.tool, call.capability, call.scope, call.arguments
            )
            assert cloned.request_id == call.request_id
            object.__setattr__(self, "call", cloned)
        elif target == "result_registration":
            copied = ToolRegistration(
                registration.name, registration.capability,
                registration.effect, registration.backend_id, backend,
            )
            object.__setattr__(self, "registration", copied)
        elif target == "result_bound_id":
            object.__setattr__(
                self, "bound_action_id", _clone(self.bound_action_id)
            )
        elif target == "registry_revision":
            registry._revision = _clone(registry._revision)
        elif target == "call_scope":
            object.__setattr__(call, "scope", "different-scope")
        elif target == "registration_backend_id":
            object.__setattr__(
                registration, "backend_id", _clone(registration.backend_id)
            )
        else:
            object.__setattr__(registration, "effect", Effect.READ)

    monkeypatch.setattr(BoundAction, "__init__", reflected_init)
    with pytest.raises(ValueError, match="changed|drifted"):
        registry.bind(call)
    assert backend.calls == 0


def test_untampered_bound_action_is_exact_and_deterministic() -> None:
    backend, registration, registry, call = _fixture()
    first = registry.bind(call)
    second = registry.bind(call)
    assert first.call is call
    assert first.registration is registration
    assert first.registry_revision is registry.revision
    assert second.bound_action_id == first.bound_action_id
    assert backend.calls == 0
