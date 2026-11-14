"""Run546: synthetic READ recovery never gains post-review authority."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_read_recovery_schedule as mod

REQ = "req_" + "e" * 32
FIRST = "step_" + "1" * 16
SECOND = "step_" + "2" * 16


def _recover():
    return mod.schedule_detached_read_recovery(REQ, (
        mod.ReadRecoveryStep(FIRST, "math.sum", (), "FAILED"),
        mod.ReadRecoveryStep(SECOND, "math.sum", (FIRST,), "NOT_STARTED"),
    ))


def test_failed_mock_branch_remains_inert():
    report = _recover()
    assert tuple(item.disposition for item in report.decisions) == (
        "TERMINAL_FAILURE", "HOLD_FAILED",
    )
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.external_outcome_verified is False


@pytest.mark.parametrize("prior", (
    "dispatch_authorized",
    "automatic_replay_authorized",
))
def test_last_false_denial_cannot_swap_prior_false_descriptor(monkeypatch, prior):
    def malicious(_self):
        monkeypatch.setattr(
            mod.DetachedReadRecoverySchedule, prior,
            property(lambda _report: False),
        )
        return False

    monkeypatch.setattr(
        mod.DetachedReadRecoverySchedule, "external_outcome_verified",
        property(malicious),
    )
    with pytest.raises(
        mod.DetachedReadRecoveryRejected,
        match=r"(descriptor changed|altered before return)",
    ):
        _recover()


def test_false_denial_cannot_replace_one_decision_carrier(monkeypatch):
    # A substituted class-level lookup hook is refused before any instance
    # getter can mutate a previously built decision carrier.
    original_getattribute = mod.DetachedReadRecoverySchedule.__getattribute__
    callbacks = []

    def malicious(self, name):
        callbacks.append(name)
        if name == "external_outcome_verified":
            old = original_getattribute(self, "decisions")[0]
            object.__setattr__(old, "disposition", "".join(
                ("TERMINAL", "_FAILURE"),
            ))
            return False
        return original_getattribute(self, name)

    monkeypatch.setattr(
        mod.DetachedReadRecoverySchedule, "__getattribute__", malicious,
    )
    with pytest.raises(
        mod.DetachedReadRecoveryRejected, match="authority descriptor changed",
    ):
        _recover()
    assert callbacks == []


def test_true_authority_is_still_denied(monkeypatch):
    monkeypatch.setattr(
        mod.DetachedReadRecoverySchedule, "dispatch_authorized",
        property(lambda _report: True),
    )
    with pytest.raises(mod.DetachedReadRecoveryRejected, match="descriptor changed"):
        _recover()
