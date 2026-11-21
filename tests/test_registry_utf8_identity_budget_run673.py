"""Registry identity size is exact UTF-8 bytes, not code points.

Only inert disconnected backends are constructed. No backend is executed.
"""
from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("identity budget must never dispatch a backend")


def _make(backend, **changes):
    args = {
        "name": "fixture.reader",
        "capability": "offline.read",
        "effect": Effect.READ,
        "backend_id": "disconnected",
        "backend": backend,
    }
    args.update(changes)
    return ToolRegistration(**args)


@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
@pytest.mark.parametrize("value", ("é" * 129, "あ" * 86, "invalid\ud800"))
def test_multibyte_or_surrogate_registration_rejected_at_entry(field, value):
    backend = NeverExecute()
    pattern = "valid UTF-8" if "invalid" in value else "registry identifier budget"
    with pytest.raises(ValueError, match=pattern):
        _make(backend, **{field: value})
    assert backend.calls == 0


@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
@pytest.mark.parametrize("value", ("é" * 128, "あ" * 85 + "a"))
def test_exact_256_byte_identity_still_builds_deterministically(field, value):
    backend = NeverExecute()
    assert len(value.encode("utf-8")) == 256
    registration = _make(backend, **{field: value})
    first = ToolRegistry((registration,))
    second = ToolRegistry((registration,))
    assert first.revision == second.revision
    assert first.get(registration.name) is registration
    call = ToolCall(registration.name, registration.capability, "local")
    assert first.bind(call).bound_action_id == second.bind(call).bound_action_id
    assert backend.calls == 0


def test_lookup_rejects_invalid_unicode_before_registry_access():
    backend = NeverExecute()
    registry = ToolRegistry((_make(backend),))
    for invalid in ("é" * 129, "invalid\ud800"):
        with pytest.raises(ValueError):
            registry.get(invalid)
    assert registry.get("fixture.reader").backend is backend
    assert backend.calls == 0
