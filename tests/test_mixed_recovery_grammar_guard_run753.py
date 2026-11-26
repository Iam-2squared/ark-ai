"""Mixed recovery grammar and step budgets cannot be rebound by local callbacks.

All fixtures are disconnected; neither a READY label nor a receipt authorizes
real execution, automatic retry, human approval, or historical attribution.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_write_recovery_fence as fence

_PLAN = "plan_" + "a" * 64
_READ = "step_" + "1" * 16
_WRITE = "step_" + "2" * 16
_RESULT = "b" * 64
_SLOT = "slot_" + "c" * 64


def _claims():
    return (
        fence.OfflineRecoveryStepClaim(_READ, "READ", (), "SUCCEEDED", _RESULT),
        fence.OfflineRecoveryStepClaim(
            _WRITE, "WRITE", (_READ,), "PENDING", reservation_id=_SLOT,
        ),
    )


@pytest.mark.parametrize("constant", (
    "_PLAN", "_STEP", "_SHA", "_SLOT", "_STATES", "_MAX_STEPS",
))
def test_rebound_mixed_grammar_or_budget_is_fail_closed(monkeypatch, constant):
    claim = _claims()
    replacement = (
        1000 if constant == "_MAX_STEPS" else
        frozenset(("PENDING", "SUCCEEDED", "INJECTED"))
        if constant == "_STATES" else object()
    )
    with monkeypatch.context() as patch:
        patch.setattr(fence, constant, replacement)
        with pytest.raises(
            fence.OfflineRecoveryFenceRejected, match="grammar or budget changed",
        ):
            fence.review_disconnected_recovery_fence(_PLAN, claim)
    result = fence.review_disconnected_recovery_fence(_PLAN, claim)
    assert tuple(row.code for row in result.decisions) == (
        "COMPLETE_UNVERIFIED", "QUARANTINE_RESERVED_WRITE",
    )
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.write_authorized is False
    assert result.external_outcome_verified is False


def test_untrusted_plan_id_never_reaches_substituted_matcher(monkeypatch):
    seen = []

    class ExfiltratingMatcher:
        def fullmatch(self, value):
            seen.append(value)
            raise AssertionError("untrusted plan passed to injected matcher")

    with monkeypatch.context() as patch:
        patch.setattr(fence, "_PLAN", ExfiltratingMatcher())
        with pytest.raises(
            fence.OfflineRecoveryFenceRejected, match="grammar or budget changed",
        ):
            fence.review_disconnected_recovery_fence("private_plan", _claims())
    assert seen == []


def test_budget_and_invalid_plan_remain_rejected_without_substitution():
    with pytest.raises(fence.OfflineRecoveryFenceRejected):
        fence.review_disconnected_recovery_fence("plan_invalid", _claims())
    oversized = tuple(
        fence.OfflineRecoveryStepClaim(
            "step_" + f"{idx:016x}", "READ", (), "PENDING",
        )
        for idx in range(25)
    )
    with pytest.raises(fence.OfflineRecoveryFenceRejected):
        fence.review_disconnected_recovery_fence(_PLAN, oversized)
