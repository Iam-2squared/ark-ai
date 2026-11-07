"""Exact grace-boundary behavior across offline preview and durable quarantine.

Only the first instant *after* grace may be durably quarantined. Neither the
previous due preview nor later EXHAUSTED state grants notification or dispatch.
"""

from __future__ import annotations

import pytest

from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
)
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)
from ark.offline_schedule_resume_review import review_offline_schedule_resume


@pytest.mark.parametrize(
    ("now", "classification"),
    (
        (9_999, "NOT_DUE"),
        (10_000, "DUE_UNVERIFIED"),
        (10_500, "DUE_UNVERIFIED"),
        (10_501, "EXPIRED_QUARANTINE"),
    ),
)
def test_grace_boundary_preview_and_persistent_quarantine_agree(
    tmp_path, now, classification,
):
    sha = "a" * 64
    policy = DisconnectedSchedulePolicy(sha, 10_000, 5_000, 1, 500)
    quarantine = QuarantinePolicy(sha, 10_000, 5_000, 1, 500)
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(
        path, policy=quarantine, create=True,
    )
    genesis = genesis_quarantine_witness(quarantine)
    occurrence = derive_quarantined_occurrence(quarantine, 0)
    preview = review_offline_schedule_resume(
        ledger, policy, DisconnectedScheduleCursor(0),
        retained_quarantine=genesis, observed_now_ms=now,
    )
    assert preview.next_occurrence_id == occurrence
    assert preview.next_state == classification
    assert preview.notification_authorized is False
    assert preview.tool_execution_authorized is False
    assert preview.automatic_replay_authorized is False

    if now <= 10_500:
        with pytest.raises(ScheduleQuarantineRejected, match="not expired"):
            ledger.quarantine_expired(
                index=0, occurrence_id=occurrence,
                observed_ms=now, retained=genesis,
            )
        assert DisconnectedScheduleQuarantineLedger(
            path, policy=quarantine,
        ).inspect(retained=genesis) == genesis
    else:
        receipt = ledger.quarantine_expired(
            index=0, occurrence_id=occurrence,
            observed_ms=now, retained=genesis,
        )
        assert receipt.execution_authorized is False
        assert receipt.notification_authorized is False
        assert receipt.automatic_replay_authorized is False
        cold = DisconnectedScheduleQuarantineLedger(path, policy=quarantine)
        retained = receipt.witness
        assert cold.inspect(retained=retained) == retained
        after = review_offline_schedule_resume(
            cold, policy, DisconnectedScheduleCursor(1, occurrence),
            retained_quarantine=retained, observed_now_ms=now,
        )
        assert after.next_state == "EXHAUSTED"
        assert after.next_occurrence_id is None
        assert after.notification_authorized is False
        assert after.tool_execution_authorized is False
        assert after.automatic_replay_authorized is False
