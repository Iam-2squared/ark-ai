"""Disconnected READ planning must reject forged result constructors.

All input is synthetic; READY_MOCK_ONLY never authorizes backend dispatch.
"""

import pytest

from ark.agency import disconnected_read_recovery_schedule as module

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16


def _review():
    return module.schedule_detached_read_recovery(
        _REQUEST,
        (module.ReadRecoveryStep(_STEP, "math.sum", (), "NOT_STARTED"),),
    )


@pytest.mark.parametrize("carrier", ("decision", "schedule"))
def test_preinstalled_hostile_result_initializer_never_runs(
    monkeypatch, carrier,
):
    target = (
        module.ReadRecoveryDecision
        if carrier == "decision" else module.DetachedReadRecoverySchedule
    )
    executed = []

    def hostile(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("forged recovery initializer executed")

    monkeypatch.setattr(target, "__init__", hostile)
    with pytest.raises(
        module.DetachedReadRecoveryRejected, match="authority descriptor changed"
    ):
        _review()
    assert executed == []


def test_substituted_digest_callback_cannot_execute_final_schedule_initializer(
    monkeypatch,
):
    executed = []
    injected = []
    original_sha = module.hashlib.sha256

    def hostile(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("forged recovery initializer executed")

    def mutate_digest(payload=b""):
        if payload.startswith(module._DOMAIN):
            injected.append(True)
            monkeypatch.setattr(
                module.DetachedReadRecoverySchedule, "__init__", hostile,
            )
        return original_sha(payload)

    monkeypatch.setattr(module.hashlib, "sha256", mutate_digest)
    with pytest.raises(
        module.DetachedReadRecoveryRejected, match="authority descriptor changed"
    ):
        _review()
    # The import-pinned SHA implementation is checked before its callback runs.
    assert injected == []
    assert executed == []


def test_normal_detached_recovery_keeps_only_mock_hint():
    result = _review()
    assert result.decisions[0].disposition == "READY_MOCK_ONLY"
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_verified is False
