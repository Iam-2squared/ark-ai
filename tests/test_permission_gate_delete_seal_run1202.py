"""Run1202: PermissionGate slot deletion is denied and class-pinned."""

from __future__ import annotations

import pytest

from ark.agency import policy
from ark.agency.contracts import PermissionDenied
from ark.agency.policy import PermissionGate


def test_sealed_permission_gate_rejects_deletion_of_every_state_slot() -> None:
    gate = PermissionGate()

    for member in (
        "_consumed_tokens",
        "_token_lock",
        "_consumed_tokens_epoch",
        "_token_lock_epoch",
        "_sealed",
    ):
        with pytest.raises(AttributeError, match="PermissionGate state is immutable"):
            delattr(gate, member)

    policy._assert_gate_instance_epoch(gate)


def test_permission_gate_pins_original_deletion_guard_before_authorize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = PermissionGate()
    invoked: list[str] = []

    def substituted(self: PermissionGate, name: str) -> None:
        invoked.append(name)
        raise AssertionError("substituted deletion guard must not execute")

    monkeypatch.setattr(PermissionGate, "__delattr__", substituted)

    with pytest.raises(
        PermissionDenied,
        match="PermissionGate implementation identity changed",
    ):
        gate.authorize(None, None, (), now_ms=0)  # type: ignore[arg-type]

    assert invoked == []
