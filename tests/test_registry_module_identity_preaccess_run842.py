"""Registry digest modules are pinned before executable member lookup.

Synthetic registry and mock backend only; never authorizes or executes tools.
"""

from __future__ import annotations

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("tool backend must remain disconnected")


class HostileModule:
    def __init__(self) -> None:
        self.reads: list[str] = []

    def __getattr__(self, name: str) -> object:
        self.reads.append(name)
        raise AssertionError("substituted module member was evaluated")


def _fixture():
    backend = NeverExecute()
    entry = ToolRegistration(
        "offline.read", "offline.read", Effect.READ, "mock:local", backend,
    )
    registry = ToolRegistry((entry,))
    call = ToolCall("offline.read", "offline.read", "fixture.private", {})
    return backend, entry, registry, call


@pytest.mark.parametrize("module_name", ("hashlib", "json"))
@pytest.mark.parametrize("operation", ("construct", "revision", "resolve", "bind"))
def test_swapped_digest_module_rejected_without_member_or_backend_access(
    monkeypatch, module_name: str, operation: str,
) -> None:
    backend, entry, registry, call = _fixture()
    hostile = HostileModule()
    with monkeypatch.context() as patch:
        patch.setattr(registry_module, module_name, hostile)
        with pytest.raises(
            ValueError, match="registry digest dependencies changed",
        ):
            if operation == "construct":
                ToolRegistry((entry,))
            elif operation == "revision":
                _ = registry.revision
            elif operation == "resolve":
                registry.resolve(call)
            else:
                registry.bind(call)
    assert hostile.reads == []
    assert backend.calls == 0


def test_intact_registry_module_contract_binds_without_execution() -> None:
    backend, entry, registry, call = _fixture()
    bound = registry.bind(call)
    assert bound.registration is entry
    assert bound.registry_revision == registry.revision
    assert backend.calls == 0
