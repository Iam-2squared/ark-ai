"""Frozen ToolRegistry fixture regression; disconnected, never dispatches backends."""

import json
import random
from pathlib import Path

import pytest

from ark.agency import Effect, ToolCall, ToolRegistration, ToolRegistry


def _fixture(name):
    return json.loads((Path(__file__).parent / "fixtures" / name).read_text("utf-8"))


class _SentinelBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("registry identity checks must never execute tools")


def _entries(rows, backend):
    return [
        ToolRegistration(
            name=row["name"],
            capability=row["capability"],
            effect=Effect(row["effect"]),
            backend_id=row["backend_id"],
            backend=backend,
        )
        for row in rows
    ]


def test_committed_revision_and_128_order_permutations():
    fixture = _fixture("tool_registry_v1.json")
    backend = _SentinelBackend()
    entries = _entries(fixture["tools"], backend)
    registry = ToolRegistry(entries)
    assert registry.revision == fixture["expected_registry_revision"]
    assert tuple(registry.registrations) == ("files.read", "files.write")
    assert registry.get("files.read") is entries[0]
    rng = random.Random(20261013)
    for _ in range(128):
        shuffled = list(entries)
        rng.shuffle(shuffled)
        assert ToolRegistry(shuffled).revision == fixture["expected_registry_revision"]
    assert backend.calls == 0


def test_committed_bound_action_vectors_are_semantically_separated():
    fixture = _fixture("tool_registry_bound_action_v1.json")
    baseline = _fixture("tool_registry_v1.json")
    request = fixture["request"]
    call = ToolCall(
        request["tool"], request["capability"], request["scope"], request["arguments"]
    )
    assert call.request_id == request["expected_request_id"]
    backend = _SentinelBackend()
    action_ids = set()
    for case in fixture["cases"]:
        rows = [dict(row) for row in baseline["tools"]]
        for row in rows:
            if row["name"] == case["tool"]:
                row["backend_id"] = case["backend_id"]
                row["effect"] = case["effect"]
        registry = ToolRegistry(_entries(rows, backend))
        binding = registry.bind(call)
        assert registry.revision == case["registry_revision"]
        assert binding.registry_revision == case["registry_revision"]
        assert binding.bound_action_id == case["expected_bound_action_id"]
        action_ids.add(binding.bound_action_id)
    assert len(action_ids) == len(fixture["cases"])
    assert backend.calls == 0


def test_registry_rejects_without_backend_execution():
    backend = _SentinelBackend()
    entries = _entries(_fixture("tool_registry_v1.json")["tools"], backend)
    registry = ToolRegistry(entries)
    with pytest.raises(ValueError, match="duplicate tool"):
        ToolRegistry(entries + [entries[0]])
    with pytest.raises(KeyError):
        registry.get("unknown.tool")
    with pytest.raises(ValueError, match="capability"):
        registry.bind(ToolCall("files.write", "wrong.capability", "workspace:a"))
    with pytest.raises(TypeError):
        registry.bind(object())
    with pytest.raises(TypeError):
        registry.registrations["files.read"] = entries[0]
    assert backend.calls == 0
