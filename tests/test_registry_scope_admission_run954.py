"""Registry-bound scope preflight is stricter than frozen ToolCall v1.

No registered backend may be invoked by identity binding or rejection.
"""

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _DisconnectedBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registry identity must never dispatch")


def _registry(effect: Effect) -> tuple[ToolRegistry, _DisconnectedBackend]:
    backend = _DisconnectedBackend()
    registry = ToolRegistry((
        ToolRegistration("offline.tool", "offline.tool", effect, "mock.v1", backend),
    ))
    return registry, backend


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
@pytest.mark.parametrize("method", ("resolve", "bind"))
def test_registry_rejects_nul_scope_without_backend_calls(
    effect: Effect, method: str,
) -> None:
    registry, backend = _registry(effect)
    call = ToolCall("offline.tool", "offline.tool", "private\x00other")
    with pytest.raises(ValueError, match="NUL separator"):
        getattr(registry, method)(call)
    assert backend.calls == 0


@pytest.mark.parametrize("method", ("resolve", "bind"))
def test_registry_rejects_unpaired_surrogate_scope_without_backend_calls(
    method: str,
) -> None:
    registry, backend = _registry(Effect.WRITE)
    call = ToolCall("offline.tool", "offline.tool", "private\ud800")
    with pytest.raises(ValueError, match="valid UTF-8"):
        getattr(registry, method)(call)
    assert backend.calls == 0


@pytest.mark.parametrize("method", ("resolve", "bind"))
def test_reflected_nul_scope_cannot_be_bound(method: str) -> None:
    registry, backend = _registry(Effect.WRITE)
    call = ToolCall("offline.tool", "offline.tool", "private")
    object.__setattr__(call, "scope", "private\x00other")
    with pytest.raises(ValueError, match="NUL separator"):
        getattr(registry, method)(call)
    assert backend.calls == 0


def test_multibyte_scope_keeps_deterministic_bound_identity() -> None:
    registry, backend = _registry(Effect.READ)
    call = ToolCall("offline.tool", "offline.tool", "端末内:個人")
    first = registry.bind(call)
    second = registry.bind(call)
    assert first.bound_action_id == second.bound_action_id
    assert first.call.scope == "端末内:個人"
    assert first.registration.effect is Effect.READ
    assert backend.calls == 0
