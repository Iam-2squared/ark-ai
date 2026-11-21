"""Scheduled COMMIT-UNKNOWN triage pins local SQLite and disposition protocol.

The scheduler is never started; synthetic expirations remain quarantined.
"""

from __future__ import annotations

import pytest

import ark.offline_schedule_unknown_quarantine_review as review
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)

_POLICY = QuarantinePolicy("a" * 64, 1000, 10000, 3, 1000)


def _attempt(ledger):
    return review.review_schedule_unknown_quarantine(
        ledger,
        _POLICY,
        genesis_quarantine_witness(_POLICY),
        index=0,
        occurrence_id=derive_quarantined_occurrence(_POLICY, 0),
        observed_ms=3000,
    )


@pytest.mark.parametrize(
    "rebound", ("review_sqlite", "ledger_sqlite", "decision_states"),
)
def test_rebound_quarantine_protocol_refused_before_private_read(
    tmp_path, monkeypatch, rebound,
):
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=_POLICY, create=True,
    )
    with monkeypatch.context() as patch:
        if rebound == "review_sqlite":
            patch.setattr(review, "sqlite3", object())
        elif rebound == "ledger_sqlite":
            patch.setattr(review.module, "sqlite3", object())
        else:
            patch.setattr(review, "_STATES", ("UNCHANGED",))
        with pytest.raises(
            review.ScheduleUnknownQuarantineRejected, match="protocol changed",
        ):
            _attempt(ledger)


def test_unchanged_quarantine_still_has_no_notification_or_replay(tmp_path):
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=_POLICY, create=True,
    )
    result = _attempt(ledger)
    assert result.local_state == "UNCHANGED"
    assert result.execution_authorized is False
    assert result.notification_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.trusted_clock_verified is False
    assert result.consent_verified is False
    assert result.manual_review_required is True
