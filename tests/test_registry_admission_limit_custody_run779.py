"""Registry admission budgets are import-time security constraints.

Synthetic tool identities only: no backend.execute is ever called, no grant,
real external effect, or durable permission is created.
"""

from __future__ import annotations

import pytest

import ark.agency.registry as registry
from ark.agency.contracts import Effect


class InertBackend:
    def execute(self, call):
        raise AssertionError("disconnected fixture backend must never execute")


def _registration(backend=None):
    return registry.ToolRegistration(
        "synthetic.read", "synthetic.read", Effect.READ,
        "mock-only", backend if backend is not None else InertBackend(),
    )


@pytest.mark.parametrize(
    ("limit_name", "replacement"),
    (
        ("_MAX_REGISTRATIONS", 257),
        ("_MAX_REGISTRATIONS", True),
        ("_MAX_REGISTRATIONS", 0),
        ("_MAX_REGISTRATION_TEXT", 257),
        ("_MAX_REGISTRATION_TEXT", True),
        ("_MAX_REGISTRATION_TEXT", 0),
    ),
)
def test_retargeted_registration_budgets_denied_before_backend_inspection(
    monkeypatch, limit_name, replacement,
):
    with monkeypatch.context() as patch:
        patch.setattr(registry, limit_name, replacement)
        # If preflight fails to notice the edited limit, the invalid backend
        # would be inspected. Its failure is NOT the expected denial.
        with pytest.raises(ValueError, match="registry admission limits changed"):
            _registration(object())
        with pytest.raises(ValueError, match="registry admission limits changed"):
            registry.ToolRegistry(())

    valid = _registration()
    fresh = registry.ToolRegistry((valid,))
    assert len(fresh.registrations) == 1
    assert fresh.revision.startswith("tools_")


@pytest.mark.parametrize("limit_name", ("_MAX_REGISTRATIONS", "_MAX_REGISTRATION_TEXT"))
def test_preexisting_registry_denies_policy_limit_drift_before_identity_read(
    monkeypatch, limit_name,
):
    bound = registry.ToolRegistry((_registration(),))
    original_revision = bound.revision
    with monkeypatch.context() as patch:
        patch.setattr(registry, limit_name, -1)
        with pytest.raises(ValueError, match="registry admission limits changed"):
            _ = bound.revision

    assert bound.revision == original_revision
