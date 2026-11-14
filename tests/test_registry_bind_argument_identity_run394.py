"""Registry-bound identifiers must retain their original argument carrier.

Only local mock backend descriptors are inspected; no execute call is allowed.
Value-equal reflected replacement is still a change of caller input epoch.
"""

from types import MappingProxyType

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("registry binding must never execute a backend")


def _fixture():
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("offline.write", "fixture.write", Effect.WRITE, "mock:v1", backend),
    ))
    call = ToolCall(
        "offline.write", "fixture.write", "private:synthetic",
        {"nested": {"key": [1, 2]}, "flag": True},
    )
    return backend, registry, call


def test_stable_argument_carrier_preserves_deterministic_binding():
    backend, registry, call = _fixture()
    original = call.arguments
    one = registry.bind(call)
    two = registry.bind(call)
    assert call.arguments is original
    assert one.call is call
    assert one.bound_action_id == two.bound_action_id
    assert one.registry_revision == registry.revision
    assert backend.calls == 0


@pytest.mark.parametrize("replacement", ("plain", "proxy", "nested"))
def test_post_resolve_value_equal_argument_rebinding_is_rejected(
    monkeypatch, replacement,
):
    backend, registry, call = _fixture()
    original = registry.resolve
    original_args = call.arguments
    original_request = call.request_id

    def changed_after_resolution(argument):
        resolved = original(argument)
        if replacement == "plain":
            clone = dict(original_args)
        elif replacement == "proxy":
            clone = MappingProxyType(dict(original_args))
        else:
            clone = MappingProxyType({
                "nested": {"key": [1, 2]}, "flag": True,
            })
        object.__setattr__(call, "arguments", clone)
        assert call.arguments is not original_args
        assert call.request_id == original_request
        return resolved

    monkeypatch.setattr(registry, "resolve", changed_after_resolution)
    with pytest.raises(ValueError, match="ToolCall identity changed"):
        registry.bind(call)
    assert backend.calls == 0


def test_direct_resolution_also_rejects_value_equal_argument_rebinding(monkeypatch):
    backend, registry, call = _fixture()
    original = registry.get

    def changed_during_get(name):
        object.__setattr__(call, "arguments", dict(call.arguments))
        return original(name)

    monkeypatch.setattr(registry, "get", changed_during_get)
    with pytest.raises(ValueError, match="ToolCall identity changed"):
        registry.resolve(call)
    assert backend.calls == 0
