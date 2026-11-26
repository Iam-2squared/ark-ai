"""Synthetic proactive readiness results reject forged carriers before callbacks.

The prepared ledger, startup snapshot and observation digests are all local
fixtures. No notification, live device, external execution or consent occurs.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

import ark.proactive_startup_fence_review as mod
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
)
from ark.startup_readiness_lease_review import SyntheticReadinessRequirement
from ark.startup_readiness_review import (
    StartupComponent,
    evaluate_startup_readiness,
)


def _case(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "prepared.sqlite")
    policy = SyntheticTriggerPolicy(
        "synthetic", "notes", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-1"),
        StartupComponent("scheduler", ("memory",), schema_revision="scheduler-1"),
    ))
    requirements = (
        SyntheticReadinessRequirement("memory", "memory-1"),
        SyntheticReadinessRequirement("scheduler", "scheduler-1"),
    )
    return ledger, receipt, policy, snapshot, requirements


def _review(case):
    return mod.review_synthetic_proactive_startup(
        *case, source_digest="a" * 64, observation_digest="b" * 64,
        captured_at_ms=98, now_ms=100, max_startup_age_ms=5,
        max_observation_age_ms=10,
    )


_RESULT_FIELDS = (
    "trigger_id", "readiness_digest", "trigger_history_digest",
    "checked_at_ms",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")


@pytest.mark.parametrize(
    "field", (*_RESULT_FIELDS, *(hook for hook in _HOOKS if hook != "__new__")),
)
def test_substituted_result_carrier_rejected_before_first_read(
    tmp_path, monkeypatch, field,
):
    case = _case(tmp_path)
    executed = []

    def forbidden(*_args, **_kwargs):
        executed.append("counterfeit carrier")
        raise AssertionError("counterfeit result callback executed")

    def unexpected_read(*_args, **_kwargs):
        executed.append("private readiness/trigger read")
        raise AssertionError("review entered before carrier check")

    cls = mod.SyntheticProactiveStartupReview
    # pytest.MonkeyPatch restores inherited __new__ by *assigning* it onto
    # the class, making object.__new__ receive dataclass constructor args in
    # later tests. Preserve exact class-dict absence instead.
    existed = field in vars(cls)
    original = vars(cls).get(field)
    try:
        setattr(
            cls, field,
            property(forbidden) if field in _RESULT_FIELDS else forbidden,
        )
        monkeypatch.setattr(mod, "review_synthetic_startup_lease", unexpected_read)
        monkeypatch.setattr(mod, "review_prepared_trigger_freshness", unexpected_read)
        with pytest.raises(
            mod.SyntheticProactiveStartupRejected,
            match="authority descriptor epoch changed",
        ):
            _review(case)
        assert executed == []
    finally:
        if existed:
            setattr(cls, field, original)
        else:
            delattr(cls, field)


@pytest.mark.parametrize("field", ("__init__", "trigger_id", "__getattribute__"))
def test_readiness_callback_cannot_install_result_carrier_before_trigger_read(
    tmp_path, monkeypatch, field,
):
    case = _case(tmp_path)
    original_readiness = mod.review_synthetic_startup_lease
    seen = []
    cls = mod.SyntheticProactiveStartupReview
    existed = field in vars(cls)
    original = vars(cls).get(field)

    def forbidden(*_args, **_kwargs):
        seen.append("counterfeit carrier")
        raise AssertionError("counterfeit result callback executed")

    def reentrant(*args, **kwargs):
        seen.append("readiness")
        report = original_readiness(*args, **kwargs)
        setattr(
            cls, field,
            property(forbidden) if field == "trigger_id" else forbidden,
        )
        return report

    def unexpected_trigger(*_args, **_kwargs):
        seen.append("trigger")
        raise AssertionError("trigger inspected after counterfeit carrier")

    monkeypatch.setattr(mod, "review_synthetic_startup_lease", reentrant)
    monkeypatch.setattr(mod, "review_prepared_trigger_freshness", unexpected_trigger)
    try:
        with pytest.raises(
            mod.SyntheticProactiveStartupRejected,
            match="authority descriptor epoch changed",
        ):
            _review(case)
        assert seen == ["readiness"]
    finally:
        if existed:
            setattr(cls, field, original)
        else:
            delattr(cls, field)



def test_new_slot_substitution_denied_in_separate_python_process():
    # Rebinding and then deleting an inherited __new__ permanently changes
    # CPython type's allocation slot in this process (including on Windows).
    # Test the original-class mutation in an isolated interpreter so later
    # normal-construction tests cannot be poisoned by pytest teardown.
    script = """
import ark.proactive_startup_fence_review as mod
calls = []
def forbidden(*args, **kwargs):
    calls.append("forged __new__ callback")
    raise AssertionError("forged constructor executed")
mod.SyntheticProactiveStartupReview.__new__ = forbidden
try:
    mod._require_original_authorities()
except mod.SyntheticProactiveStartupRejected as exc:
    assert "authority descriptor epoch changed" in str(exc)
else:
    raise AssertionError("forged __new__ accepted")
assert calls == []
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_unmodified_receipt_still_denies_dispatch(tmp_path):
    receipt = _review(_case(tmp_path))
    assert receipt.startup_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
