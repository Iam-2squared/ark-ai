"""Registry constructor consumes bounded, first-seen tool identities only.

No backend is executed. These synthetic reflection fixtures do not establish
trusted backend identity, durable approval or real action authority.
"""

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverBackend:
    def execute(self, _call: ToolCall) -> object:
        raise AssertionError("registry construction must never execute a backend")


def _registration(index: int, backend=None) -> ToolRegistration:
    return ToolRegistration(
        f"tool-{index}", "offline-read", Effect.READ, f"mock-{index}",
        backend if backend is not None else NeverBackend(),
    )


def test_oversized_registration_generator_stops_at_first_extra_item():
    advanced = 0

    def registrations():
        nonlocal advanced
        for index in range(registry_module._MAX_REGISTRATIONS + 12):
            advanced += 1
            yield _registration(index)

    with pytest.raises(ValueError, match="construction budget exceeded"):
        ToolRegistry(registrations())
    assert advanced == registry_module._MAX_REGISTRATIONS + 1


def test_exact_registration_budget_still_builds_a_disconnected_registry():
    items = (_registration(index) for index in range(
        registry_module._MAX_REGISTRATIONS
    ))
    built = ToolRegistry(items)
    assert len(built.registrations) == registry_module._MAX_REGISTRATIONS
    assert built.get("tool-0").backend_id == "mock-0"
    assert built.get(f"tool-{registry_module._MAX_REGISTRATIONS - 1}")


@pytest.mark.parametrize("field,replacement", (
    ("name", "replacement"),
    ("capability", "replacement"),
    ("effect", Effect.WRITE),
    ("backend_id", "replacement"),
))
def test_transient_previous_registration_drift_rejected_before_restoration(
    field, replacement,
):
    first = _registration(0)
    second = _registration(1)
    original = getattr(first, field)
    advanced = []

    def registrations():
        yield first
        advanced.append(2)
        object.__setattr__(first, field, replacement)
        yield second
        advanced.append(3)
        object.__setattr__(first, field, original)
        yield _registration(2)

    with pytest.raises(ValueError, match="changed during registry construction"):
        ToolRegistry(registrations())
    assert advanced == [2]


def test_registration_mutated_during_generator_exhaustion_is_rejected():
    entry = _registration(0)

    def registrations():
        try:
            yield entry
        finally:
            object.__setattr__(entry, "backend_id", "after-finally")

    with pytest.raises(ValueError, match="changed during registry construction"):
        ToolRegistry(registrations())


def test_backend_interface_drift_during_materialization_is_rejected(monkeypatch):
    first = _registration(0)
    second = _registration(1)

    def replacement(_self, _call):
        raise AssertionError("registry must not dispatch")

    def registrations():
        yield first
        monkeypatch.setattr(NeverBackend, "execute", replacement)
        yield second

    with pytest.raises(ValueError, match="changed during registry construction"):
        ToolRegistry(registrations())


def test_revision_serialization_cannot_rebase_first_observed_registration(
    monkeypatch,
):
    first = _registration(0)
    original_canonical = registry_module._canonical_json

    def mutating_revision(payload):
        object.__setattr__(first, "effect", Effect.WRITE)
        return original_canonical(payload)

    monkeypatch.setattr(registry_module, "_canonical_json", mutating_revision)
    with pytest.raises(ValueError, match="changed during registry construction"):
        ToolRegistry((first,))


def test_unmodified_registry_remains_order_independent():
    first, second = _registration(0), _registration(1)
    left = ToolRegistry((first, second))
    right = ToolRegistry((second, first))
    assert left.revision == right.revision
    assert left.bind(ToolCall("tool-0", "offline-read", "local")).bound_action_id == (
        right.bind(ToolCall("tool-0", "offline-read", "local")).bound_action_id
    )
