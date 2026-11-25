"""Run1240: ToolRegistry slot deletion and guard identity stay fail-closed."""

from __future__ import annotations

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry
import pytest


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


def test_all_registry_slots_refuse_ordinary_deletion_after_seal() -> None:
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
        with pytest.raises(AttributeError, match="ToolRegistry is immutable"):
            delattr(registry, slot)

    assert registry.revision == original_revision
    assert registry.bind(call).registry_revision == original_revision
    assert backend.calls == 0


def test_reflective_registration_slot_deletion_fails_before_binding() -> None:
    registry, backend, call = _registry()
    object.__delattr__(registry, "_registrations")

    # object.__delattr__ deliberately bypasses the ordinary guard. The public
    # binding path must still fail before returning an identity or dispatching.
    with pytest.raises(AttributeError):
        registry.bind(call)
    assert backend.calls == 0


def test_replaced_class_delete_guard_is_rejected_before_registry_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, backend, _call = _registry()
    invoked: list[str] = []

    def hostile_delete(*_args: object, **_kwargs: object) -> None:
        invoked.append("delete")
        raise AssertionError("substituted deletion guard must not execute")

    monkeypatch.setattr(ToolRegistry, "__delattr__", hostile_delete)

    with pytest.raises(ValueError, match="registry instance immutability contract changed"):
        _ = registry.revision

    assert invoked == []
    assert backend.calls == 0
