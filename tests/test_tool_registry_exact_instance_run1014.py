"""Run1009: ToolRegistry rejects subclasses before touching instance state.

An immutable mapping does not make a subclass immutable: overridden attribute
lookup can substitute the revision, registrations or bound-action state read by
inherited methods. Construction and every public resolution path therefore
require the exact import-original ToolRegistry type before instance access.
The tests use inert registrations and never execute a backend.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("registry identity test must not dispatch")


def _registration() -> ToolRegistration:
    return ToolRegistration(
        "fixture.tool",
        "fixture.read",
        Effect.READ,
        "disconnected.mock.v1",
        _NeverExecute(),
    )


def test_registry_constructor_rejects_subclass_before_registration_iteration():
    touched: list[str] = []

    class _ObservedRegistry(ToolRegistry):
        def __getattribute__(self, name: str):
            touched.append(name)
            raise AssertionError("subclass instance lookup must not run")

    def registrations():
        touched.append("iterated")
        yield _registration()

    with pytest.raises(TypeError, match="exact ToolRegistry"):
        _ObservedRegistry(registrations())
    assert touched == []


def test_inherited_registry_entrypoints_reject_uninitialized_subclass_before_lookup():
    touched: list[str] = []

    class _ObservedRegistry(ToolRegistry):
        def __getattribute__(self, name: str):
            touched.append(name)
            raise AssertionError("subclass instance lookup must not run")

    foreign = object.__new__(_ObservedRegistry)
    call = ToolCall("fixture.tool", "fixture.read", "synthetic:scope", {"n": 1})

    operations = (
        lambda: ToolRegistry._assert_registration_epoch(foreign),
        lambda: ToolRegistry.revision.fget(foreign),
        lambda: ToolRegistry.registrations.fget(foreign),
        lambda: ToolRegistry.get(foreign, "fixture.tool"),
        lambda: ToolRegistry.resolve(foreign, call),
        lambda: ToolRegistry.bind(foreign, call),
    )
    for operation in operations:
        with pytest.raises(TypeError, match="exact ToolRegistry"):
            operation()

    assert touched == []
