"""Registry binding refuses swapped digest dependencies before private identity reads.

Only local mock backends are used. These checks neither attest backend identity
nor authorize tool dispatch, durable approvals, or an external side effect.
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
        raise AssertionError("registry must not dispatch a backend")


def _fixture() -> tuple[ToolRegistration, ToolRegistry, ToolCall, NeverExecute]:
    backend = NeverExecute()
    registration = ToolRegistration(
        "fixture.read", "fixture.read", Effect.READ, "offline:fixture", backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall(
        "fixture.read", "fixture.read", "private:synthetic",
        {"private": "synthetic-secret-fixture"},
    )
    return registration, registry, call, backend


def _install_dependency(patch, dependency: str, attempted: list[str]) -> None:
    def hostile(*_args, **_kwargs):
        attempted.append(dependency)
        raise AssertionError("substituted dependency must never run")

    if dependency == "sha256":
        patch.setattr(registry_module.hashlib, "sha256", hostile)
    else:
        patch.setattr(registry_module.json, "dumps", hostile)


@pytest.mark.parametrize("dependency", ("sha256", "json.dumps"))
@pytest.mark.parametrize(
    "operation", ("construct", "revision", "registrations", "get", "resolve", "bind"),
)
def test_preinstalled_digest_callback_is_rejected_without_dispatch(
    monkeypatch: pytest.MonkeyPatch, dependency: str, operation: str,
) -> None:
    registration, registry, call, backend = _fixture()
    attempted: list[str] = []
    with monkeypatch.context() as patch:
        _install_dependency(patch, dependency, attempted)
        with pytest.raises(ValueError, match="registry digest dependencies changed"):
            if operation == "construct":
                ToolRegistry((registration,))
            elif operation == "revision":
                _ = registry.revision
            elif operation == "registrations":
                _ = registry.registrations
            elif operation == "get":
                registry.get("fixture.read")
            elif operation == "resolve":
                registry.resolve(call)
            else:
                registry.bind(call)
    assert attempted == []
    assert backend.calls == 0


@pytest.mark.parametrize("dependency", ("sha256", "json.dumps"))
def test_generator_mutation_is_denied_before_next_registration_read(
    monkeypatch: pytest.MonkeyPatch, dependency: str,
) -> None:
    first, _, _, backend = _fixture()
    second = ToolRegistration(
        "fixture.other", "fixture.read", Effect.READ, "offline:other", backend,
    )
    attempted: list[str] = []
    advanced: list[str] = []

    with monkeypatch.context() as patch:
        def registrations():
            yield first
            advanced.append("dependency changed")
            _install_dependency(patch, dependency, attempted)
            yield second
            advanced.append("must not advance")

        with pytest.raises(ValueError, match="registry digest dependencies changed"):
            ToolRegistry(registrations())

    assert advanced == ["dependency changed"]
    assert attempted == []
    assert backend.calls == 0


@pytest.mark.parametrize("dependency", ("sha256", "json.dumps"))
@pytest.mark.parametrize("operation", ("resolve", "bind"))
def test_lookup_mutation_is_denied_before_second_call_digest(
    monkeypatch: pytest.MonkeyPatch, dependency: str, operation: str,
) -> None:
    _, registry, call, backend = _fixture()
    original_get = registry.get
    attempted: list[str] = []

    with monkeypatch.context() as patch:
        def swap_after_lookup(name: str):
            result = original_get(name)
            _install_dependency(patch, dependency, attempted)
            return result

        patch.setattr(registry, "get", swap_after_lookup)
        with pytest.raises(ValueError, match="registry digest dependencies changed"):
            getattr(registry, operation)(call)

    assert attempted == []
    assert backend.calls == 0


def test_original_digest_dependencies_preserve_deterministic_mock_identity() -> None:
    registration, registry, call, backend = _fixture()
    one, two = registry.bind(call), registry.bind(call)
    assert one.registration is two.registration is registration
    assert one.call is two.call is call
    assert one.bound_action_id == two.bound_action_id
    assert one.registry_revision == two.registry_revision == registry.revision
    assert backend.calls == 0
