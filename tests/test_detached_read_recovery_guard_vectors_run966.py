"""Run966: shortened control vectors cannot omit disconnected READ vetoes."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_read_recovery_schedule as recovery

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16


@pytest.mark.parametrize("name", (
    "_RESULT_HOOKS",
    "_DECISION_FIELDS",
    "_SCHEDULE_FIELDS",
    "_DENIAL_NAMES",
))
def test_guard_vector_rebinding_fails_before_untrusted_step_getter(
    monkeypatch, name: str,
) -> None:
    step = recovery.ReadRecoveryStep(
        _STEP, "math.sum", (), "NOT_STARTED", None,
    )
    calls: list[str] = []

    def poisoned_getter(_self, key: str):
        calls.append(key)
        raise AssertionError("untrusted step getter was executed")

    with monkeypatch.context() as patch:
        patch.setattr(recovery, name, ())
        patch.setattr(
            recovery.ReadRecoveryStep, "__getattribute__", poisoned_getter,
        )
        with pytest.raises(
            recovery.DetachedReadRecoveryRejected,
            match="authority descriptor changed",
        ):
            recovery.schedule_detached_read_recovery(_REQUEST, (step,))
    assert calls == []


def test_unmodified_guard_vectors_produce_only_mock_hints() -> None:
    step = recovery.ReadRecoveryStep(
        _STEP, "math.sum", (), "NOT_STARTED", None,
    )
    result = recovery.schedule_detached_read_recovery(_REQUEST, (step,))
    assert result.decisions[0].disposition == "READY_MOCK_ONLY"
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_verified is False
