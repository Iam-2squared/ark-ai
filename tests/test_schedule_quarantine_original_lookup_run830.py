"""Restart quarantine triage refuses patched ledger and SQLite ingress hooks.

All test rows are local synthetic quarantine fixtures. No trusted clock,
notification, consent, scheduler dispatch, or replay authority is exercised.
"""

from __future__ import annotations

import pytest

import ark.offline_schedule_unknown_quarantine_review as triage
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)

_POLICY = QuarantinePolicy("a" * 64, 1_000, 10_000, 3, 1_000)


def _fixture(tmp_path):
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "synthetic-quarantine.sqlite", policy=_POLICY, create=True,
    )
    return ledger, genesis_quarantine_witness(_POLICY)


def _review(ledger, before):
    return triage.review_schedule_unknown_quarantine(
        ledger, _POLICY, before, index=0,
        occurrence_id=derive_quarantined_occurrence(_POLICY, 0),
        observed_ms=3_000,
    )


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_mutated_ledger_lookup_is_refused_before_any_private_path_read(
    tmp_path, monkeypatch, hook,
):
    ledger, before = _fixture(tmp_path)
    invocations = []

    def forbidden(*args, **kwargs):
        invocations.append(hook)
        raise AssertionError("a replaced ledger lookup hook executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            DisconnectedScheduleQuarantineLedger, hook, forbidden, raising=False,
        )
        with pytest.raises(
            triage.ScheduleUnknownQuarantineRejected,
            match="quarantine triage protocol changed",
        ):
            _review(ledger, before)

    assert invocations == []
    result = _review(ledger, before)
    assert result.local_state == "UNCHANGED"
    assert result.execution_authorized is False
    assert result.automatic_replay_authorized is False


def test_rebound_sqlite_connector_refused_before_connection(tmp_path, monkeypatch):
    ledger, before = _fixture(tmp_path)
    invocations = []

    def forbidden(*args, **kwargs):
        invocations.append("sqlite")
        raise AssertionError("unreviewed sqlite connector executed")

    with monkeypatch.context() as patch:
        patch.setattr(triage.sqlite3, "connect", forbidden)
        with pytest.raises(
            triage.ScheduleUnknownQuarantineRejected,
            match="quarantine triage protocol changed",
        ):
            _review(ledger, before)

    assert invocations == []
    result = _review(ledger, before)
    assert result.local_state == "UNCHANGED"
    assert result.consent_verified is False
    assert result.notification_authorized is False
