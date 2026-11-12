"""Quarantine inventory rejects poisoned local protocol with no equality hooks.

No SQLite, user data, clock, tool or automatic replay is involved.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_recovery_quarantine_inventory as inventory


class PoisonEquality:
    def __init__(self, calls):
        self.calls = calls

    def __eq__(self, other):
        self.calls.append("eq")
        raise AssertionError("untrusted protocol equality was called")

    def __ne__(self, other):
        self.calls.append("ne")
        raise AssertionError("untrusted protocol inequality was called")


@pytest.mark.parametrize("name", (
    "_SHA", "_OCC", "_MEMORY_DISPOSITIONS", "_ATOMIC_STATES",
    "_MAX_OCCURRENCES", "_MAX_STEPS", "_MAX_STEP_ID_BYTES",
))
def test_quarantine_protocol_rejects_poisoned_constant_without_comparison(
    monkeypatch, name,
):
    calls = []
    with monkeypatch.context() as patch:
        patch.setattr(inventory, name, PoisonEquality(calls))
        with pytest.raises(
            inventory.DisconnectedRecoveryInventoryRejected,
            match="quarantine inventory protocol changed",
        ):
            inventory.review_disconnected_recovery_quarantine(
                object(), object(), (),
            )
    assert calls == []


def test_normal_invalid_inventory_input_still_refuses_without_authority():
    with pytest.raises(
        inventory.DisconnectedRecoveryInventoryRejected,
        match="exact bounded local recovery reports required",
    ):
        inventory.review_disconnected_recovery_quarantine(object(), object(), ())
