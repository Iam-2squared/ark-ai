"""Run1100: direct ToolRegistry revision, immutability and binding checks.

Only inert synthetic backends are registered. No backend is executed.
"""

from __future__ import annotations

from types import MappingProxyType

import pytest

from ark.agency import BoundAction, Effect, ToolCall, ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registry contract tests must not execute a backend")


def _registry() -> tuple[ToolRegistry, NeverExecute, NeverExecute]:
    reader = NeverExecute()
    writer = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "local:reader", reader),
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local:writer", writer),
    ))
    return registry, reader, writer


def test_revision_is_deterministic_and_registration_view_is_immutable() -> None:
    reader = NeverExecute()
    writer = NeverExecute()
    read = ToolRegistration("reader", "fixture.read", Effect.READ, "local:reader", reader)
    write = ToolRegistration("writer", "fixture.write", Effect.WRITE, "local:writer", writer)

    first = ToolRegistry((read, write))
    reordered = ToolRegistry((write, read))
    changed_identity = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "local:reader-v2", reader),
        write,
    ))

    assert first.revision == reordered.revision
    assert first.revision != changed_identity.revision
    assert tuple(first.registrations) == ("reader", "writer")
    assert type(first.registrations) is MappingProxyType
    with pytest.raises(TypeError):
        first.registrations["injected"] = read  # type: ignore[index]
    assert reader.calls == writer.calls == 0


def test_bind_returns_registry_bound_request_identity_without_dispatch() -> None:
    registry, reader, writer = _registry()
    call = ToolCall("reader", "fixture.read", "local:scope", {"n": 1})

    first = registry.bind(call)
    second = registry.bind(call)
    changed_request = registry.bind(
        ToolCall("reader", "fixture.read", "local:scope", {"n": 2}),
    )

    assert type(first) is BoundAction
    assert first is not second
    assert first.registry_revision == registry.revision
    assert first.call is call
    assert first.registration is registry.get("reader")
    assert first.bound_action_id == second.bound_action_id
    assert first.bound_action_id != changed_request.bound_action_id
    assert reader.calls == writer.calls == 0


def test_registry_construction_rejects_mutated_earlier_generator_item() -> None:
    first_backend = NeverExecute()
    second_backend = NeverExecute()
    first = ToolRegistration(
        "first", "fixture.read", Effect.READ, "local:first", first_backend,
    )
    second = ToolRegistration(
        "second", "fixture.read", Effect.READ, "local:second", second_backend,
    )

    def registrations():
        yield first
        # Generator resumption is a callback boundary between yielded items.
        object.__setattr__(first, "backend_id", "local:mutated")
        yield second

    with pytest.raises(ValueError, match="registered tool changed during registry construction"):
        ToolRegistry(registrations())
    assert first_backend.calls == second_backend.calls == 0


def test_registry_rejects_equal_valued_mapping_replacement_and_call_subclasses() -> None:
    registry, _, _ = _registry()
    original = registry.registrations
    object.__setattr__(registry, "_registrations", MappingProxyType(dict(original)))
    with pytest.raises(ValueError, match="identity map changed"):
        _ = registry.revision

    fresh, reader, writer = _registry()

    class ForeignCall(ToolCall):
        pass

    foreign = ForeignCall("reader", "fixture.read", "local:scope", {"n": 1})
    with pytest.raises(TypeError, match="exact ToolCall"):
        fresh.resolve(foreign)
    with pytest.raises(TypeError, match="exact ToolCall"):
        fresh.bind(foreign)
    assert reader.calls == writer.calls == 0
