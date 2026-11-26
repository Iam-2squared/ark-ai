"""Run1297: ToolRegistry assignment seal and guard identity stay fail-closed."""

from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registry integrity tests must never dispatch")


def _registry() -> tuple[ToolRegistry, _NeverExecute, ToolCall]:
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.read",
            "fixture.read",
            Effect.READ,
            "disconnected.mock.v1",
            backend,
        ),
    ))
    call = ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"n": 1})
    return registry, backend, call


def test_all_registry_slots_refuse_ordinary_assignment_after_seal() -> None:
    registry, backend, call = _registry()
    original_revision = registry.revision

    for slot in (
        "_registrations",
        "_registry_mapping_epoch",
        "_registration_epoch",
        "_revision",
        "_revision_epoch",
        "_sealed",
    ):
        current = object.__getattribute__(registry, slot)
        with pytest.raises(AttributeError, match="ToolRegistry is immutable"):
            setattr(registry, slot, current)

    assert registry.revision == original_revision
    assert registry.bind(call).registry_revision == original_revision
    assert backend.calls == 0


def test_replaced_class_assignment_guard_is_rejected_before_registry_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, backend, _call = _registry()
    invoked: list[str] = []

    def hostile_set(*_args: object, **_kwargs: object) -> None:
        invoked.append("set")
        raise AssertionError("substituted assignment guard must not execute")

    monkeypatch.setattr(ToolRegistry, "__setattr__", hostile_set)

    with pytest.raises(
        ValueError,
        match="registry instance immutability contract changed",
    ):
        _ = registry.revision

    assert invoked == []
    assert backend.calls == 0
