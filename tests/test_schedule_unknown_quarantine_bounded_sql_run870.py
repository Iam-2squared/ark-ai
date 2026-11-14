"""Synthetic scheduled UNKNOWN triage selects at most two occurrence rows.

Fixture-only SQLite data; no scheduler, notification, consent or external action.
"""
from __future__ import annotations

from contextlib import closing

import pytest

import ark.offline_schedule_unknown_quarantine_review as triage
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)

POLICY = QuarantinePolicy("a" * 64, 1000, 10000, 3, 1000)


@pytest.mark.parametrize(
    ("record_index", "requested_index", "observed_ms", "expected"),
    (
        (None, 0, 3000, "UNCHANGED"),
        (0, 0, 3000, "LOCALLY_QUARANTINED"),
        (0, 1, 13000, "ADVANCED_OTHER"),
    ),
)
def test_unknown_review_uses_bounded_sql_membership(
    tmp_path, monkeypatch, record_index, requested_index, observed_ms, expected,
):
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=POLICY, create=True,
    )
    retained = genesis_quarantine_witness(POLICY)
    if record_index is not None:
        ledger.quarantine_expired(
            index=record_index,
            occurrence_id=derive_quarantined_occurrence(POLICY, record_index),
            observed_ms=3000,
            retained=retained,
        )

    seen_sql = []

    def tracing_close(conn):
        conn.set_trace_callback(seen_sql.append)
        return closing(conn)

    with monkeypatch.context() as patch:
        patch.setattr(triage, "closing", tracing_close)
        result = triage.review_schedule_unknown_quarantine(
            ledger, POLICY, retained, index=requested_index,
            occurrence_id=derive_quarantined_occurrence(POLICY, requested_index),
            observed_ms=observed_ms,
        )

    queries = [s for s in seen_sql if "WHERE occurrence_id=" in s]
    assert len(queries) == 1
    assert "LIMIT 2" in queries[0]
    assert result.local_state == expected
    assert result.execution_authorized is False
    assert result.notification_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.manual_review_required is True
