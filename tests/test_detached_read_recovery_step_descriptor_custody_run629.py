"""Exact supplied READ step slots must not run substituted accessors.

Only synthetic decisions are calculated; no backend, replay or external action.
"""

import pytest

from ark.agency import disconnected_read_recovery_schedule as recovery

_REQUEST = "req_" + "b" * 32
_STEP = "step_" + "1" * 16


def _step():
    return recovery.ReadRecoveryStep(_STEP, "math.sum", (), "NOT_STARTED")


def _run(row):
    return recovery.schedule_detached_read_recovery(_REQUEST, (row,))


class _Trap:
    def __init__(self, hits):
        self.hits = hits

    def __get__(self, instance, owner=None):
        self.hits.append("ran")
        raise AssertionError("substituted READ input descriptor executed")


@pytest.mark.parametrize("field", (
    "step_id", "operation", "depends_on", "state", "result_sha256",
))
def test_preinstalled_step_slot_trap_is_rejected_before_execution(monkeypatch, field):
    row = _step()
    hits = []
    monkeypatch.setattr(recovery.ReadRecoveryStep, field, _Trap(hits))
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected,
        match="authority descriptor changed",
    ):
        _run(row)
    assert hits == []


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_preinstalled_lookup_hook_is_rejected_before_execution(monkeypatch, hook):
    row = _step()
    hits = []

    def hostile(*args):
        hits.append("ran")
        raise AssertionError("substituted READ lookup hook executed")

    monkeypatch.setattr(recovery.ReadRecoveryStep, hook, hostile, raising=False)
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected,
        match="authority descriptor changed",
    ):
        _run(row)
    assert hits == []


@pytest.mark.parametrize("field", ("step_id", "state"))
def test_substituted_digest_hook_cannot_install_late_step_slot_trap(monkeypatch, field):
    row = _step()
    hits = []
    injected = []
    native_sha = recovery.hashlib.sha256

    def mutate_after_digest(payload=b""):
        if payload.startswith(recovery._DOMAIN):
            injected.append(True)
            monkeypatch.setattr(recovery.ReadRecoveryStep, field, _Trap(hits))
        return native_sha(payload)

    monkeypatch.setattr(recovery.hashlib, "sha256", mutate_after_digest)
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected,
        match="authority descriptor changed",
    ):
        _run(row)
    # A replaced SHA callback is denied before it can mutate any step field.
    assert injected == []
    assert hits == []


def test_original_steps_keep_terminal_hold_and_unrelated_mock_hint():
    failed = "step_" + "1" * 16
    child = "step_" + "2" * 16
    independent = "step_" + "3" * 16
    rows = (
        recovery.ReadRecoveryStep(failed, "math.sum", (), "FAILED"),
        recovery.ReadRecoveryStep(child, "text.find", (failed,), "NOT_STARTED"),
        recovery.ReadRecoveryStep(independent, "json.inspect", (), "NOT_STARTED"),
    )
    first = recovery.schedule_detached_read_recovery(_REQUEST, rows)
    again = recovery.schedule_detached_read_recovery(_REQUEST, rows)
    assert first.schedule_digest == again.schedule_digest
    assert [(d.step_id, d.disposition) for d in first.decisions] == [
        (failed, "TERMINAL_FAILURE"),
        (child, "HOLD_FAILED"),
        (independent, "READY_MOCK_ONLY"),
    ]
    assert first.dispatch_authorized is False
    assert first.automatic_replay_authorized is False
    assert first.external_outcome_verified is False
