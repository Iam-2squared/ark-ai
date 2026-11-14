"""Retained Planner mock READ-cycle receipts remain inert across revalidation."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_read_cycle_receipt_recheck as recheck
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.disconnected_read_cycle import simulate_registered_read_cycle
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class ForbiddenBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("a detached diagnostic must not invoke a backend")


def _inputs(*, independent: bool = False, effect: Effect = Effect.READ):
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", effect, "mock:1", backend),
    ))
    plan = PlanGraph((
        PlanStep("a", ToolCall("reader", "fixture.read", "local", {"secret": "canary"})),
        PlanStep(
            "b", ToolCall("reader", "fixture.read", "local", {"item": 2}),
            () if independent else ("a",),
        ),
    ))
    grants = (CapabilityGrant("fixture.read", "local", 300),)
    return plan, registry, PermissionGate(), grants, backend


def _receipt(plan, registry, gate, grants):
    return simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )


@pytest.mark.parametrize("independent", (False, True))
def test_valid_stored_receipt_rederives_without_effects(independent: bool) -> None:
    plan, registry, gate, grants, backend = _inputs(independent=independent)
    before = plan.status_digest()
    receipt = _receipt(plan, registry, gate, grants)
    for _ in range(2):
        assert recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=100,
        ) is None
    assert backend.calls == 0
    assert not gate._consumed_tokens
    assert plan.status_digest() == before
    assert all(s.state is StepState.PENDING for s in plan.statuses().values())
    assert "canary" not in repr(receipt)


@pytest.mark.parametrize(
    "field,value",
    (
        ("topology_digest", "plan_" + "0" * 64),
        ("registry_revision", "tools_" + "0" * 64),
        ("wave_bound_step_hashes", (("0" * 64,),)),
        ("final_status_digest", "status_" + "0" * 64),
        ("fingerprint", "0" * 64),
    ),
)
def test_tampered_retained_receipt_is_denied(field: str, value: object) -> None:
    plan, registry, gate, grants, backend = _inputs()
    receipt = replace(_receipt(plan, registry, gate, grants), **{field: value})
    with pytest.raises(recheck.DisconnectedReadCycleReceiptRejected, match="differs"):
        recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0


@pytest.mark.parametrize("invalid", (None, object(), {}, "receipt"))
def test_only_exact_receipt_type_accepted(invalid: object) -> None:
    plan, registry, gate, grants, backend = _inputs()
    with pytest.raises(recheck.DisconnectedReadCycleReceiptRejected, match="exact bounded"):
        recheck.verify_disconnected_read_cycle_receipt(
            invalid, plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0


@pytest.mark.parametrize("bad_now", (True, -1, 2**63, 100.0, "100"))
def test_synthetic_clock_needs_exact_bounded_integer(bad_now: object) -> None:
    plan, registry, gate, grants, backend = _inputs()
    receipt = _receipt(plan, registry, gate, grants)
    with pytest.raises(recheck.DisconnectedReadCycleReceiptRejected, match="exact bounded"):
        recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=bad_now,
        )
    assert backend.calls == 0


@pytest.mark.parametrize("condition", ("expired", "wrong_scope", "missing", "write"))
def test_revalidation_cannot_grant_expired_or_write_access(condition: str) -> None:
    plan, registry, gate, grants, backend = _inputs()
    receipt = _receipt(plan, registry, gate, grants)
    if condition == "write":
        other = ToolRegistry((
            ToolRegistration("reader", "fixture.read", Effect.WRITE, "mock:1", backend),
        ))
        registry = other
    elif condition == "expired":
        grants = (CapabilityGrant("fixture.read", "local", 99),)
    elif condition == "wrong_scope":
        grants = (CapabilityGrant("fixture.read", "different", 300),)
    else:
        grants = ()
    with pytest.raises(recheck.DisconnectedReadCycleReceiptRejected, match="simulation denied"):
        recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0


def test_nonpending_plan_never_replays_a_mock_completion() -> None:
    plan, registry, gate, grants, backend = _inputs()
    receipt = _receipt(plan, registry, gate, grants)
    plan.transition("a", StepState.RUNNING, expected_revision=0)
    with pytest.raises(recheck.DisconnectedReadCycleReceiptRejected, match="simulation denied"):
        recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0


def test_retained_receipt_reflectively_mutated_during_fresh_simulation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, registry, gate, grants, backend = _inputs()
    receipt = _receipt(plan, registry, gate, grants)
    original = recheck.simulate_registered_read_cycle

    def altered(*args, **kwargs):
        fresh = original(*args, **kwargs)
        object.__setattr__(receipt, "fingerprint", "f" * 64)
        return fresh

    monkeypatch.setattr(recheck, "simulate_registered_read_cycle", altered)
    with pytest.raises(recheck.DisconnectedReadCycleReceiptRejected, match="changed"):
        recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0


def test_equal_value_grant_carrier_replacement_during_fresh_simulation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, registry, gate, grants, backend = _inputs()
    receipt = _receipt(plan, registry, gate, grants)
    original = recheck.simulate_registered_read_cycle
    grant = grants[0]

    def altered(*args, **kwargs):
        fresh = original(*args, **kwargs)
        replacement = ("_" + grant.scope)[1:]
        assert replacement == grant.scope and replacement is not grant.scope
        object.__setattr__(grant, "scope", replacement)
        return fresh

    monkeypatch.setattr(recheck, "simulate_registered_read_cycle", altered)
    with pytest.raises(recheck.DisconnectedReadCycleReceiptRejected, match="changed"):
        recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0


def test_fresh_receipt_substitution_cannot_validate_old_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, registry, gate, grants, backend = _inputs()
    receipt = _receipt(plan, registry, gate, grants)
    monkeypatch.setattr(
        recheck, "simulate_registered_read_cycle",
        lambda *args, **kwargs: replace(receipt, fingerprint="0" * 64),
    )
    with pytest.raises(recheck.DisconnectedReadCycleReceiptRejected, match="differs"):
        recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0


def test_authority_property_spoofing_cannot_validate_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, registry, gate, grants, backend = _inputs()
    receipt = _receipt(plan, registry, gate, grants)
    monkeypatch.setattr(
        type(receipt), "automatic_replay_authorized", property(lambda self: True),
    )
    with pytest.raises(recheck.DisconnectedReadCycleReceiptRejected, match="changed"):
        recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0
