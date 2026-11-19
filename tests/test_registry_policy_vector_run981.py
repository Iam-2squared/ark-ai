"""Opt-in immutable ToolRegistry refuses shortened identity vectors.

Synthetic backend only; no execute() call, real tool, token spend or external
action is permitted by registry resolution or binding.
"""

from __future__ import annotations

import pytest

import ark.agency.registry as registry
from ark.agency.contracts import Effect, ToolCall


class Backend:
    def execute(self, call):
        raise AssertionError("registered backend must never execute")


def _fixture():
    registration = registry.ToolRegistration(
        "math.sum", "math", Effect.READ, "mock-only", Backend(),
    )
    registered = registry.ToolRegistry((registration,))
    call = ToolCall("math.sum", "math", "local", {"values": [1]})
    return registered, call


@pytest.mark.parametrize("vector,phase,expected", (
    ("_REGISTRATION_FIELDS", "registration", "tool registration contract changed"),
    ("_REGISTRATION_METHODS", "registration", "tool registration contract changed"),
    ("_REGISTRATION_HOOKS", "registration", "tool registration contract changed"),
    ("_TOOL_CALL_ORIGINALS", "resolve", "ToolCall registry policy vector changed"),
    ("_TOOL_CALL_INPUT_FIELDS", "resolve", "ToolCall registry policy vector changed"),
    ("_TOOL_CALL_LOOKUP_HOOKS", "resolve", "ToolCall registry policy vector changed"),
    ("_BOUND_FIELDS", "bind", "registry bound policy vector changed"),
    ("_BOUND_HOOKS", "bind", "registry bound policy vector changed"),
))
@pytest.mark.parametrize("mutation", ("empty", "reverse", "equal_rebound"))
def test_rebound_registry_control_vector_cannot_skip_descriptor_custody(
    monkeypatch, vector, phase, expected, mutation,
):
    registered, call = _fixture()
    original = getattr(registry, vector)
    assert len(original) >= 2
    if mutation == "empty":
        forged = ()
    elif mutation == "reverse":
        forged = tuple(reversed(original))
    else:
        forged = tuple(list(original))
        assert forged == original and forged is not original

    with monkeypatch.context() as patch:
        patch.setattr(registry, vector, forged)
        with pytest.raises(ValueError, match=expected):
            if phase == "registration":
                registry.ToolRegistration(
                    "math.extra", "math", Effect.READ, "mock-only", Backend(),
                )
            elif phase == "resolve":
                registered.resolve(call)
            else:
                registered.bind(call)


def test_shortened_registration_fields_cannot_hide_callback_backend(
    monkeypatch,
):
    called = []

    def forged(self):
        called.append(True)
        raise AssertionError("unverified registry descriptor executed")

    with monkeypatch.context() as patch:
        patch.setattr(registry, "_REGISTRATION_FIELDS", ())
        patch.setattr(registry.ToolRegistration, "backend", property(forged))
        with pytest.raises(ValueError, match="tool registration contract changed"):
            registry.ToolRegistration(
                "math.extra", "math", Effect.READ, "mock-only", Backend(),
            )
    assert called == []


def test_unmodified_registry_binds_without_exec_or_permission():
    registered, call = _fixture()
    bound = registered.bind(call)
    assert bound.call is call
    assert bound.registration.name == "math.sum"
    assert bound.registry_revision == registered.revision
    assert len(bound.bound_action_id) > 0
