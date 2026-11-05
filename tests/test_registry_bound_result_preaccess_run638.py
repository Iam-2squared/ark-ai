"""Fail closed before executing rebound BoundAction descriptors.

No ToolBackend method may be called by registration, resolution or binding.
The class is restored by monkeypatch after each test.
"""

from __future__ import annotations

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import BoundAction, ToolRegistration, ToolRegistry


class ForbiddenBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("tool execution is forbidden")


def _case():
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "mock.write", "offline.write", Effect.WRITE, "mock", backend,
        ),
    ))
    call = ToolCall("mock.write", "offline.write", "local", {"a": "fixture"})
    return registry, call, backend


@pytest.mark.parametrize(
    ("kind", "name"),
    (
        ("slot", "registry_revision"),
        ("slot", "call"),
        ("slot", "registration"),
        ("slot", "bound_action_id"),
        ("hook", "__getattribute__"),
        ("hook", "__getattr__"),
    ),
)
def test_preinstalled_bound_result_descriptor_never_executes(
    monkeypatch, kind, name,
):
    registry, call, backend = _case()
    triggered = []

    def rogue(*_args, **_kwargs):
        triggered.append(name)
        raise AssertionError("untrusted bound-result descriptor executed")

    if kind == "slot":
        monkeypatch.setattr(BoundAction, name, property(rogue))
    elif name in vars(BoundAction):
        monkeypatch.setattr(BoundAction, name, rogue)
    else:
        # __new__ / __getattribute__ are inherited. monkeypatch.setattr
        # would restore them as new OWN attributes, contaminating later
        # tests with an altered class dictionary and misleading failures.
        replacement = staticmethod(rogue) if name == "__new__" else rogue
        setattr(BoundAction, name, replacement)
        try:
            with pytest.raises(ValueError, match="bound result constructor changed"):
                registry.bind(call)
        finally:
            delattr(BoundAction, name)
        assert triggered == []
        assert backend.calls == 0
        return

    with pytest.raises(ValueError, match="bound result constructor changed"):
        registry.bind(call)
    assert triggered == []
    assert backend.calls == 0


def test_export_replacement_is_rejected_before_constructing_an_impostor(
    monkeypatch,
):
    registry, call, backend = _case()
    constructed = []

    class Impostor:
        def __init__(self, *_args, **_kwargs):
            constructed.append("constructed")
            raise AssertionError("impostor must not be constructed")

    # Reassigning a slotted class's __new__ alters CPython's tp_new slot
    # even after deleting that attribute. Instead verify that replacing
    # the exported class is rejected, with no global constructor mutation.
    monkeypatch.setattr(registry_module, "BoundAction", Impostor)
    with pytest.raises(ValueError, match="bound result constructor changed"):
        registry.bind(call)
    assert constructed == []
    assert backend.calls == 0


def test_reentrant_registry_revision_cannot_rebind_result_field(
    monkeypatch,
):
    registry, call, backend = _case()
    original_revision = registry._compute_revision
    executed = []

    def rogue(*_args, **_kwargs):
        executed.append("descriptor invoked")
        raise AssertionError("rebound result field executed")

    def mutate_during_revision(registrations):
        result = original_revision(registrations)
        monkeypatch.setattr(BoundAction, "registration", property(rogue))
        return result

    monkeypatch.setattr(registry, "_compute_revision", mutate_during_revision)
    with pytest.raises(ValueError, match="bound result constructor changed"):
        registry.bind(call)
    assert executed == []
    assert backend.calls == 0


def test_unmodified_binding_preserves_registry_identity_without_execution():
    registry, call, backend = _case()
    bound = registry.bind(call)
    assert type(bound) is BoundAction
    assert bound.call is call
    assert bound.registration is registry.registrations["mock.write"]
    assert bound.registry_revision == registry.revision
    assert bound.bound_action_id.startswith("bound_")
    assert backend.calls == 0
