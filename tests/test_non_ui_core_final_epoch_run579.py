"""Non-UI guards against late Planner, Memory, and policy identity drift.

Synthetic, disconnected fixtures only. No backend execution, authority,
physical effects, real consent, trusted clock, or COMMIT retry is claimed.
"""

from __future__ import annotations

import builtins

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.agency import planner as planner_module
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    PlanConflictError,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.memory import ambiguous_commit_pair_review as pair_module


def _plan() -> planner_module.PlanGraph:
    root = PlanStep("root", ToolCall("fixture", "offline", "local"))
    child = PlanStep(
        "child", ToolCall("fixture", "offline", "local", {"child": True}),
        depends_on=("root",),
    )
    return planner_module.PlanGraph((root, child))


def test_final_detached_planner_copy_cannot_corrupt_committed_state(monkeypatch):
    graph = _plan()
    native = planner_module.replace

    def changed(value, **updates):
        copied = native(value, **updates)
        if not updates and value.step_id == "root":
            object.__setattr__(graph._status["root"], "revision", 123)
        return copied

    monkeypatch.setattr(planner_module, "replace", changed)
    with pytest.raises(PlanConflictError, match="outside transition"):
        graph.transition("root", StepState.RUNNING, expected_revision=0)


def test_final_detached_planner_copy_cannot_forge_success(monkeypatch):
    graph = _plan()
    native = planner_module.replace

    def forged(value, **updates):
        copied = native(value, **updates)
        if not updates and value.step_id == "root":
            object.__setattr__(copied, "state", StepState.SUCCEEDED)
        return copied

    monkeypatch.setattr(planner_module, "replace", forged)
    with pytest.raises(PlanConflictError, match="result changed"):
        graph.transition("root", StepState.RUNNING, expected_revision=0)


def test_untampered_planner_transition_and_terminal_cascade():
    graph = _plan()
    started = graph.transition("root", StepState.RUNNING, expected_revision=0)
    assert (started.state, started.revision) == (StepState.RUNNING, 1)
    stopped = graph.transition("root", StepState.FAILED, expected_revision=1)
    assert (stopped.state, stopped.revision) == (StepState.FAILED, 2)
    assert graph.statuses()["child"].state is StepState.BLOCKED


@pytest.mark.parametrize("field", ("observed_row_sha256", "reconciliation_sha256"))
def test_memory_final_false_only_getter_cannot_forge_returned_receipt(
    tmp_path, monkeypatch, field,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    native = builtins.getattr
    injected = []

    def reentrant_getattr(value, name, *default):
        if (
            type(value) is pair_module.MemoryAmbiguityPair
            and name == "trusted_clock_verified"
        ):
            injected.append(name)
            object.__setattr__(value, field, "f" * 64)
        return native(value, name, *default)

    with monkeypatch.context() as patch:
        patch.setattr(pair_module, "getattr", reentrant_getattr, raising=False)
        with pytest.raises(
            pair_module.MemoryAmbiguityPairRejected, match="result changed",
        ):
            pair_module.review_memory_ambiguous_commit_pair(
                store, proposed, retained=retained,
            )
    assert injected == ["trusted_clock_verified"]


def test_untampered_memory_ambiguity_reconciliation_is_manual_only(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    receipt = pair_module.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )
    assert receipt.disposition == "LOCAL_UNCHANGED_REVIEW"
    assert receipt.automatic_retry_authorized is False
    assert receipt.caller_commit_authenticated is False


class _NeverExecute:
    def execute(self, _call):
        raise AssertionError("disconnected policy must not execute a backend")


def _policy_inputs():
    registry = ToolRegistry((
        ToolRegistration("mock", "cap", Effect.WRITE, "offline", _NeverExecute()),
    ))
    call = ToolCall("mock", "cap", "fixture", {"n": 1})
    token = OneShotAuthorization("run579-local-token", call.request_id, 1_000)
    return registry, call, token, (CapabilityGrant("cap", "fixture"),)


@pytest.mark.parametrize("interface", ("bind", "resolve", "revision", "authorize"))
def test_preinstalled_policy_class_replacement_is_denied_before_spend(
    monkeypatch, interface,
):
    registry, call, token, grants = _policy_inputs()
    gate = PermissionGate()

    def forbidden(*args, **kwargs):
        raise AssertionError("replaced authority must never run")

    with monkeypatch.context() as patch:
        if interface == "authorize":
            patch.setattr(PermissionGate, interface, forbidden)
        elif interface == "revision":
            patch.setattr(ToolRegistry, interface, property(forbidden))
        else:
            patch.setattr(ToolRegistry, interface, forbidden)
        with pytest.raises(PermissionDenied, match="implementation identity changed"):
            gate.authorize_registered(
                registry, call, grants, now_ms=10, one_shot=token,
            )
    assert gate._consumed_tokens == set()
    assert gate.authorize_registered(
        registry, call, grants, now_ms=10, one_shot=token,
    ).registration.effect is Effect.WRITE


def test_mid_grant_class_replacement_cannot_consume_token(monkeypatch):
    registry, call, token, grants = _policy_inputs()
    gate = PermissionGate()

    def forbidden(*args, **kwargs):
        raise AssertionError("substituted registry bind must not run")

    def grants_with_change():
        yield grants[0]
        monkeypatch.setattr(ToolRegistry, "bind", forbidden)

    with monkeypatch.context() as patch:
        # The local context restores the class interface for the next check.
        def changed_grants():
            yield grants[0]
            patch.setattr(ToolRegistry, "bind", forbidden)

        with pytest.raises(PermissionDenied, match="implementation identity changed"):
            gate.authorize_registered(
                registry, call, changed_grants(), now_ms=10, one_shot=token,
            )
    assert gate._consumed_tokens == set()
    gate.authorize_registered(registry, call, grants, now_ms=10, one_shot=token)


def test_instance_shadow_cannot_bypass_exact_class_authorization(monkeypatch):
    registry, call, token, grants = _policy_inputs()
    gate = PermissionGate()

    def no_op(*args, **kwargs):
        # Deliberately skips all grant and local token checks.
        return None

    monkeypatch.setattr(gate, "authorize", no_op)
    with pytest.raises(PermissionDenied, match="implementation identity changed"):
        gate.authorize_registered(
            registry, call, grants, now_ms=10, one_shot=token,
        )
    assert gate._consumed_tokens == set()
