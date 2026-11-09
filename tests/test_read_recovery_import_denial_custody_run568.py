"""Import-pinned no-dispatch custody on detached READ recovery schedules."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_read_recovery_schedule as recovery

REQUEST = "req_" + "e" * 32
STEP = "step_" + "1" * 16


def _recover():
    return recovery.schedule_detached_read_recovery(
        REQUEST, (recovery.ReadRecoveryStep(STEP, "math.sum", (), "FAILED"),),
    )


@pytest.mark.parametrize("name", recovery._DENIAL_NAMES)
@pytest.mark.parametrize("replacement", (False, True))
def test_preinstalled_denial_substitution_fails_before_hashing(
    monkeypatch, name, replacement,
):
    def forbidden(*args, **kwargs):
        pytest.fail("preinstalled authority substitution reached hashing")

    monkeypatch.setattr(
        recovery.DetachedReadRecoverySchedule, name,
        property(lambda _: replacement),
    )
    monkeypatch.setattr(recovery.hashlib, "sha256", forbidden)
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected, match="descriptor changed",
    ):
        _recover()


@pytest.mark.parametrize("name", recovery._DENIAL_NAMES)
def test_substituted_hash_callback_cannot_replace_original_denial(
    monkeypatch, name,
):
    original = recovery.hashlib.sha256
    calls = 0

    def malicious(data):
        nonlocal calls
        calls += 1
        monkeypatch.setattr(
            recovery.DetachedReadRecoverySchedule, name,
            property(lambda _: False),
        )
        return original(data)

    monkeypatch.setattr(recovery.hashlib, "sha256", malicious)
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected, match="descriptor changed",
    ):
        _recover()
    # The forged digest is not allowed to run, even once.
    assert calls == 0


def test_honest_detached_recovery_remains_inert_and_deterministic():
    first = _recover()
    second = _recover()
    assert first == second
    assert first.decisions[0].disposition == "TERMINAL_FAILURE"
    assert first.dispatch_authorized is False
    assert first.automatic_replay_authorized is False
    assert first.external_outcome_verified is False
