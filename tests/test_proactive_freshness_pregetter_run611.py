"""Disconnected proactive freshness rejects injected denial code before access.

Test ledgers are disposable; no real notification, action, or consent is involved.
"""

import pytest

import ark.proactive_synthetic_freshness_review as freshness
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _case(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "freshness-guard.sqlite")
    policy = SyntheticTriggerPolicy(
        "local", "private", "fixture", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    return ledger, policy, receipt


def _review(case):
    ledger, policy, receipt = case
    return freshness.review_prepared_trigger_freshness(
        ledger, receipt, policy,
        source_digest="a" * 64, observation_digest="b" * 64,
        now_ms=100, max_observation_age_ms=10,
    )


class _SideEffectDescriptor:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("getter")
        return False


def test_counterfeit_result_class_never_constructed(tmp_path, monkeypatch):
    case = _case(tmp_path)
    calls = []

    class Counterfeit:
        def __init__(self, *_args):
            calls.append("constructor")
            raise AssertionError("counterfeit must not construct")

    monkeypatch.setattr(freshness, "SyntheticProactiveFreshnessReview", Counterfeit)
    with pytest.raises(
        SyntheticTriggerRejected, match="freshness output carrier definition changed"
    ):
        _review(case)
    assert calls == []


@pytest.mark.parametrize("flag", freshness._FRESHNESS_DENIALS)
def test_reentrant_field_check_cannot_install_executable_flag(
    tmp_path, monkeypatch, flag,
):
    case = _case(tmp_path)
    cls = freshness._FRESHNESS_RESULT
    original = cls.__getattribute__
    calls = []
    injected = [False]

    def intervene(self, name):
        value = original(self, name)
        if name == "history" and not injected[0]:
            injected[0] = True
            monkeypatch.setattr(cls, flag, _SideEffectDescriptor(calls))
        return value

    monkeypatch.setattr(cls, "__getattribute__", intervene)
    # The changed __getattribute__ definition is detected before history
    # or denial properties are accessed. Injection code never executes.
    with pytest.raises(
        SyntheticTriggerRejected, match="freshness output carrier definition changed"
    ):
        _review(case)
    assert injected == [False]
    assert calls == []


def test_earlier_getter_cannot_arm_next_property(tmp_path, monkeypatch):
    case = _case(tmp_path)
    cls = freshness._FRESHNESS_RESULT
    original = cls.__getattribute__
    calls = []

    def intervene(self, name):
        value = original(self, name)
        if name == "notification_authorized":
            monkeypatch.setattr(
                cls, "dispatch_authorized", _SideEffectDescriptor(calls),
            )
        return value

    monkeypatch.setattr(cls, "__getattribute__", intervene)
    with pytest.raises(
        SyntheticTriggerRejected, match="freshness output carrier definition changed"
    ):
        _review(case)
    assert calls == []


def test_unmodified_freshness_is_read_only_and_deny_only(tmp_path):
    case = _case(tmp_path)
    before = case[0].path.read_bytes()
    result = _review(case)
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert case[0].path.read_bytes() == before
