"""Registered permission validators refuse altered admission inventories.

Synthetic READ/WRITE metadata only; the disconnected backend never executes.
"""

from __future__ import annotations

import pytest
from test_registered_permission_gate_run361 import _call, _grant, _registry

from ark.agency import policy
from ark.agency.contracts import Effect, PermissionDenied


@pytest.mark.parametrize(
    "name",
    (
        "_GRANT_FIELDS", "_ORIGINAL_GRANT_FIELDS",
        "_GRANT_HOOKS", "_ORIGINAL_GRANT_HOOKS",
        "_SPEC_FIELDS", "_SPEC_METHODS", "_SPEC_HOOKS",
        "_ORIGINAL_SPEC_FIELDS", "_ORIGINAL_SPEC_METHODS",
        "_ORIGINAL_SPEC_HOOKS", "_TOKEN_FIELDS", "_TOKEN_METHODS",
        "_TOKEN_HOOKS", "_ORIGINAL_TOKEN_FIELDS",
        "_ORIGINAL_TOKEN_METHODS", "_ORIGINAL_TOKEN_HOOKS",
    ),
)
@pytest.mark.parametrize("mutation", ("drop", "equal_rebind"))
def test_registered_gate_refuses_altered_validator_vectors_before_callbacks(
    monkeypatch, name, mutation,
):
    registry, backend, _ = _registry(Effect.READ)
    original = getattr(policy, name)
    replacement = (
        original[:-1] if mutation == "drop" else tuple(list(original))
    )
    assert replacement is not original

    def forbidden_grants():
        raise AssertionError("invalid validator inventory reached caller iterator")
        yield _grant()

    with monkeypatch.context() as patch:
        patch.setattr(policy, name, replacement)
        with pytest.raises(PermissionDenied, match="validator|inventory"):
            policy.PermissionGate().authorize_registered(
                registry, _call(), forbidden_grants(), now_ms=10,
            )
    assert backend.calls == 0


def test_registered_gate_untampered_read_only_remains_no_dispatch():
    registry, backend, _ = _registry(Effect.READ)
    call = _call()
    bound = policy.PermissionGate().authorize_registered(
        registry, call, (_grant(),), now_ms=10,
    )
    assert bound.registration.effect is Effect.READ
    assert backend.calls == 0


def test_registered_gate_write_without_one_shot_still_denied():
    registry, backend, _ = _registry(Effect.WRITE)
    with pytest.raises(PermissionDenied, match="one-shot"):
        policy.PermissionGate().authorize_registered(
            registry, _call(), (_grant(),), now_ms=10,
        )
    assert backend.calls == 0
