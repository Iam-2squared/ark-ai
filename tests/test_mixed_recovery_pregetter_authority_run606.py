"""No counterfeit recovery fence descriptor may run during mock WRITE triage.

Only local inert claims are used; UNKNOWN writes remain non-replayable.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_write_recovery_fence as mod

PLAN = "plan_" + "a" * 64
WRITE = "step_" + "1" * 16
CHILD = "step_" + "2" * 16
READ = "step_" + "3" * 16
_FLAGS = (
    "dispatch_authorized",
    "automatic_replay_authorized",
    "write_authorized",
    "external_outcome_verified",
)


def _claims():
    return (
        mod.OfflineRecoveryStepClaim(WRITE, "WRITE", (), "UNKNOWN"),
        mod.OfflineRecoveryStepClaim(CHILD, "READ", (WRITE,), "PENDING"),
        mod.OfflineRecoveryStepClaim(READ, "READ", (), "PENDING"),
    )


@pytest.mark.parametrize("flag", _FLAGS)
@pytest.mark.parametrize("stage", ("preinstalled", "hash_callback"))
def test_forged_false_getter_rejected_without_running_it(
    monkeypatch, flag, stage,
):
    invoked = []
    hash_callback_calls = []

    class Counterfeit:
        def __get__(self, _instance, _owner=None):
            invoked.append(flag)
            return False

    if stage == "preinstalled":
        monkeypatch.setattr(mod.OfflineRecoveryFence, flag, Counterfeit())
    else:
        real_sha256 = mod.hashlib.sha256

        def replace_after_hash(payload):
            hash_callback_calls.append(payload)
            monkeypatch.setattr(mod.OfflineRecoveryFence, flag, Counterfeit())
            return real_sha256(payload)

        monkeypatch.setattr(mod.hashlib, "sha256", replace_after_hash)

    with pytest.raises(
        mod.OfflineRecoveryFenceRejected,
        match=(
            "authority descriptor changed" if stage == "preinstalled"
            else "mixed-plan digest implementation or domain changed"
        ),
    ):
        mod.review_disconnected_recovery_fence(PLAN, _claims())
    assert invoked == []
    assert hash_callback_calls == []


def test_counterfeit_result_class_with_original_properties_rejected(
    monkeypatch,
):
    original = mod.OfflineRecoveryFence
    constructed = []

    def constructor(self, *args):
        constructed.append(args)

    properties = {name: vars(original)[name] for name in _FLAGS}
    properties["__init__"] = constructor
    counterfeit = type("CounterfeitRecoveryFence", (), properties)
    monkeypatch.setattr(mod, "OfflineRecoveryFence", counterfeit)
    with pytest.raises(
        mod.OfflineRecoveryFenceRejected,
        match="authority descriptor changed",
    ):
        mod.review_disconnected_recovery_fence(PLAN, _claims())
    assert constructed == []


def test_clean_mixed_plan_never_dispatches_unknown_write():
    view = mod.review_disconnected_recovery_fence(PLAN, _claims())
    assert tuple(item.code for item in view.decisions) == (
        "QUARANTINE_WRITE_UNKNOWN",
        "HOLD_UNCERTAIN",
        "READY_MOCK_ONLY",
    )
    assert all(getattr(view, name) is False for name in _FLAGS)
