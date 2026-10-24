"""ToolRegistry.resolve must reject caller and registry drift during lookup.

This exercises only disconnected backend descriptors; execute is never called.
"""

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def execute(self, call):
        raise AssertionError("registry resolution never executes a backend")


def _registry():
    entry = ToolRegistration(
        "offline.tool", "cap", Effect.WRITE, "fixture-backend", _NeverExecute(),
    )
    return ToolRegistry((entry,)), entry


def _call(*, capability="cap", tool="offline.tool"):
    return ToolCall(tool, capability, "local-fixture", {"k": 1})


def test_stable_resolution_is_not_execution_authority():
    registry, entry = _registry()
    assert registry.resolve(_call()) is entry
    assert registry.resolve(_call()).effect is Effect.WRITE


@pytest.mark.parametrize("change", ["tool", "capability", "scope", "arguments"])
def test_get_callback_cannot_redefine_original_call(monkeypatch, change):
    registry, _ = _registry()
    call = _call(
        tool="unknown.tool" if change == "tool" else "offline.tool",
        capability="unapproved" if change == "capability" else "cap",
    )
    original_get = registry.get

    def substitute(name):
        if change == "tool":
            object.__setattr__(call, "tool", "offline.tool")
            name = "offline.tool"
        elif change == "capability":
            object.__setattr__(call, "capability", "cap")
        elif change == "scope":
            object.__setattr__(call, "scope", "different-scope")
        else:
            object.__setattr__(call, "arguments", {"k": 1})
        return original_get(name)

    monkeypatch.setattr(registry, "get", substitute)
    with pytest.raises(ValueError, match="ToolCall identity changed"):
        registry.resolve(call)


def test_get_callback_cannot_change_registry_effect_after_validation(monkeypatch):
    registry, entry = _registry()
    original_get = registry.get

    def change_effect(name):
        result = original_get(name)
        object.__setattr__(entry, "effect", Effect.READ)
        return result

    monkeypatch.setattr(registry, "get", change_effect)
    with pytest.raises(ValueError, match="registry|registered tool"):
        registry.resolve(_call())


@pytest.mark.parametrize("mode", ["clone", "effect", "missing"])
@pytest.mark.parametrize("operation", ["resolve", "bind"])
def test_get_must_return_the_original_registered_entry(
    monkeypatch, mode, operation,
):
    registry, entry = _registry()
    if mode == "clone":
        forged = ToolRegistration(
            entry.name, entry.capability, entry.effect,
            entry.backend_id, entry.backend,
        )
    elif mode == "effect":
        forged = ToolRegistration(
            entry.name, entry.capability, Effect.READ,
            "different-backend", _NeverExecute(),
        )
    else:
        forged = None

    monkeypatch.setattr(registry, "get", lambda _name: forged)
    with pytest.raises(ValueError, match="unregistered identity"):
        getattr(registry, operation)(_call())
