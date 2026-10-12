"""Frozen, disconnected ToolRegistry identity vectors.
No backend execution, permission grant, or real action is permitted.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry

FIXTURES = Path(__file__).parent / "fixtures"

class _DisconnectedBackend:
    def __init__(self) -> None:
        self.calls = 0
    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("Registry identity must never dispatch")

def _registry(*, effect: Effect = Effect.WRITE, backend_id: str = "mock.files.write:v1"):
    reader, writer = _DisconnectedBackend(), _DisconnectedBackend()
    reg = ToolRegistry((
        ToolRegistration("files.write", "files.write", effect, backend_id, writer),
        ToolRegistration("files.read", "files.read", Effect.READ, "mock.files.read:v1", reader),
    ))
    return reg, reader, writer

def test_registry_frozen_revision_and_order_independence() -> None:
    fixture = json.loads((FIXTURES / "tool_registry_v1.json").read_text(encoding="utf-8"))
    registry, reader, writer = _registry()
    assert registry.revision == fixture["expected_registry_revision"]
    entries = tuple(registry.registrations.values())
    for seed in range(256):
        ordered = list(entries)
        random.Random(seed).shuffle(ordered)
        assert ToolRegistry(ordered).revision == registry.revision
    assert reader.calls == writer.calls == 0

@pytest.mark.parametrize("case_index", [0, 1, 2])
def test_registry_frozen_bound_action_vectors(case_index: int) -> None:
    fixture = json.loads(
        (FIXTURES / "tool_registry_bound_action_v1.json").read_text(encoding="utf-8")
    )
    case, request = fixture["cases"][case_index], fixture["request"]
    call = ToolCall(request["tool"], request["capability"], request["scope"], request["arguments"])
    assert call.request_id == request["expected_request_id"]
    registry, reader, writer = _registry(
        effect=Effect(case["effect"]), backend_id=case["backend_id"]
    )
    bound = registry.bind(call)
    assert registry.revision == case["registry_revision"]
    assert bound.registry_revision == case["registry_revision"]
    assert bound.bound_action_id == case["expected_bound_action_id"]
    assert bound.registration.effect is Effect(case["effect"])
    assert reader.calls == writer.calls == 0

def test_registry_rejects_invalid_identity_without_dispatch() -> None:
    registry, reader, writer = _registry()
    with pytest.raises(KeyError, match="unknown tool"):
        registry.get("unknown")
    with pytest.raises(ValueError, match="capability"):
        registry.bind(ToolCall("files.write", "files.read", "workspace:a"))
    with pytest.raises(TypeError, match="exact ToolCall"):
        registry.resolve(object())  # type: ignore[arg-type]
    assert reader.calls == writer.calls == 0

def test_registry_entries_and_public_mapping_are_immutable() -> None:
    registry, _, _ = _registry()
    registration = registry.get("files.read")
    with pytest.raises(TypeError):
        registry.registrations["unknown"] = registration  # type: ignore[index]
    with pytest.raises((AttributeError, TypeError)):
        registration.backend_id = "forged"  # type: ignore[misc]

def test_registry_rejects_duplicate_names_and_non_registration_values() -> None:
    registry, _, _ = _registry()
    existing = registry.get("files.read")
    with pytest.raises(ValueError, match="duplicate"):
        ToolRegistry((existing, existing))
    with pytest.raises(TypeError, match="ToolRegistration"):
        ToolRegistry((object(),))  # type: ignore[arg-type]
