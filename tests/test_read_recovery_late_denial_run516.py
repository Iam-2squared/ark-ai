"""A synthetic READ recovery schedule remains inert after its last getter.

All actions here are disconnected and simulated; READY_MOCK_ONLY never
authorizes dispatch or replay.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_read_recovery_schedule as module

_REQ = "req_" + "a" * 32
_STEP = "step_" + "1" * 16


def _row() -> module.ReadRecoveryStep:
    return module.ReadRecoveryStep(_STEP, "math.sum", (), "NOT_STARTED")


def test_stable_recovery_remains_non_authorizing() -> None:
    result = module.schedule_detached_read_recovery(_REQ, (_row(),))
    assert result.decisions[0].disposition == "READY_MOCK_ONLY"
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_verified is False


@pytest.mark.parametrize("target", ("digest", "decision", "source"))
def test_last_false_denial_getter_cannot_mutate_retained_result(
    monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    source = _row()
    called = 0

    def mutate_and_deny(schedule: module.DetachedReadRecoverySchedule) -> bool:
        nonlocal called
        called += 1
        if target == "digest":
            object.__setattr__(schedule, "schedule_digest", "f" * 64)
        elif target == "decision":
            object.__setattr__(
                schedule.decisions[0], "disposition", "QUARANTINE_UNCERTAIN",
            )
        else:
            object.__setattr__(source, "operation", "text.find")
        return False

    original_getattribute = module.DetachedReadRecoverySchedule.__getattribute__

    def intercept(self, name):
        if name == "external_outcome_verified":
            return mutate_and_deny(self)
        return original_getattribute(self, name)

    with monkeypatch.context() as patch:
        patch.setattr(
            module.DetachedReadRecoverySchedule, "__getattribute__", intercept,
        )
        with pytest.raises(
            module.DetachedReadRecoveryRejected,
            match="authority descriptor changed",
        ):
            module.schedule_detached_read_recovery(_REQ, (source,))
    # Replacement of the lookup hook is rejected before it can mutate the
    # input step or one of the newly built result carriers.
    assert called == 0
    assert source.operation == "math.sum"


def test_last_denial_getter_cannot_enable_earlier_dispatch_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        original_getattribute = (
            module.DetachedReadRecoverySchedule.__getattribute__
        )

        callbacks = []

        def intercept(self, name):
            callbacks.append(name)
            if name == "external_outcome_verified":
                patch.setattr(
                    module.DetachedReadRecoverySchedule,
                    "dispatch_authorized", property(lambda _self: True),
                )
                return False
            return original_getattribute(self, name)

        patch.setattr(
            module.DetachedReadRecoverySchedule, "__getattribute__", intercept,
        )
        with pytest.raises(
            module.DetachedReadRecoveryRejected,
            match="authority descriptor changed",
        ):
            module.schedule_detached_read_recovery(_REQ, (_row(),))
        assert callbacks == []
