"""Run750: detached READ recovery rejects class/contract substitution preaccess.

These are disconnected, untrusted synthetic histories; a READY_MOCK_ONLY
decision is not permission to dispatch or replay an actual tool.
"""

import subprocess
import sys

import pytest

from ark.agency import disconnected_read_recovery_schedule as recovery

REQUEST = "req_" + "a" * 32
STEP = "step_" + "1" * 16


def _step():
    return recovery.ReadRecoveryStep(
        STEP, "math.sum", (), "NOT_STARTED",
    )


@pytest.mark.parametrize(
    "hook", ("__init__", "__getattribute__", "__getattr__"),
)
def test_step_constructor_or_lookup_substitution_rejected_preaccess(
    monkeypatch, hook,
):
    original = _step()
    touched = []

    def poisoned(*args, **kwargs):
        touched.append((args, kwargs))
        raise AssertionError("untrusted READ step hook executed")

    with monkeypatch.context() as patch:
        patch.setattr(recovery.ReadRecoveryStep, hook, poisoned, raising=False)
        with pytest.raises(
            recovery.DetachedReadRecoveryRejected,
            match="recovery schedule authority descriptor changed",
        ):
            recovery.schedule_detached_read_recovery(REQUEST, (original,))

    assert touched == []


def test_new_hook_substitution_rejected_in_isolated_interpreter():
    # CPython does not fully restore type.__new__ allocation slots after a
    # class-level monkeypatch/undo. Keep this adversarial probe in a child
    # interpreter so every subsequent pytest test sees the original class.
    script = """
from ark.agency import disconnected_read_recovery_schedule as recovery

request = "req_" + "a" * 32
step = recovery.ReadRecoveryStep("step_" + "1" * 16, "math.sum", (), "NOT_STARTED")
assert "__new__" not in vars(recovery.ReadRecoveryStep)

def poisoned(*args, **kwargs):
    raise AssertionError("untrusted READ step __new__ executed")

recovery.ReadRecoveryStep.__new__ = poisoned
try:
    recovery.schedule_detached_read_recovery(request, (step,))
except recovery.DetachedReadRecoveryRejected as exc:
    assert "recovery schedule authority descriptor changed" in str(exc)
else:
    raise AssertionError("substituted READ __new__ was accepted")
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("vector", ("_STEP_FIELDS", "_STEP_HOOKS"))
def test_equal_value_replacement_of_reviewed_step_vector_is_rejected(
    monkeypatch, vector,
):
    original = _step()
    initial = getattr(recovery, vector)
    replacement = tuple(list(initial))
    assert replacement == initial
    assert replacement is not initial
    with monkeypatch.context() as patch:
        patch.setattr(recovery, vector, replacement)
        with pytest.raises(
            recovery.DetachedReadRecoveryRejected,
            match="recovery schedule authority descriptor changed",
        ):
            recovery.schedule_detached_read_recovery(REQUEST, (original,))


def test_original_read_history_still_yields_deny_only_mock_hint():
    result = recovery.schedule_detached_read_recovery(REQUEST, (_step(),))
    assert result.decisions[0].disposition == "READY_MOCK_ONLY"
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_verified is False
