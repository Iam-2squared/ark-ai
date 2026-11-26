"""Offline ToolRegistry backend descriptors remain inert and identity-pinned.

No backend is invoked; these fixtures do not grant permission, action authority,
external effects, or authenticated execution provenance.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("registry inspection must never execute a backend")


def _fixture():
    backend = _NeverExecute()
    entry = ToolRegistration(
        "fixture.static", "local.read", Effect.READ, "offline-only", backend,
    )
    return ToolRegistry((entry,)), entry, backend


def test_property_based_backend_is_refused_without_evaluating_getter():
    touched = []

    class _PropertyBackend:
        @property
        def execute(self):
            touched.append("property evaluated")
            raise AssertionError("do not evaluate execute property")

    with pytest.raises(TypeError, match="statically callable"):
        ToolRegistration(
            "fixture.property", "local.read", Effect.READ, "offline-only",
            _PropertyBackend(),
        )
    assert touched == []


@pytest.mark.parametrize("operation", ("bind", "resolve", "revision"))
def test_post_registration_callable_replacement_is_refused_without_dispatch(
    monkeypatch, operation,
):
    registry, _entry, backend = _fixture()
    call = ToolCall("fixture.static", "local.read", "offline", {"proof": 1})

    def replacement(self, call):
        raise AssertionError("rebound backend must not be called")

    with monkeypatch.context() as patch:
        patch.setattr(_NeverExecute, "execute", replacement)
        with pytest.raises(ValueError):
            if operation == "bind":
                registry.bind(call)
            elif operation == "resolve":
                registry.resolve(call)
            else:
                _ = registry.revision

    assert backend.calls == 0


@pytest.mark.parametrize("field", ("effect", "backend"))
def test_reflected_registration_authority_drift_is_denied(field):
    registry, entry, backend = _fixture()
    replacement = Effect.WRITE if field == "effect" else _NeverExecute()
    object.__setattr__(entry, field, replacement)
    with pytest.raises(ValueError):
        registry.bind(ToolCall("fixture.static", "local.read", "offline"))
    assert backend.calls == 0
    if field == "backend":
        assert replacement.calls == 0
