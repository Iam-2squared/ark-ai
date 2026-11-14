"""Every synthetic WRITE interruption remains UNKNOWN after a cold reopen.

Four SQLite side effects are deliberately not one atomic transaction. Reopening
all stores must not turn a persisted RUNNING state into permission to replay,
or mistake an audit/occurrence receipt for an external exactly-once effect.
"""

from __future__ import annotations

import pytest
from test_synthetic_mock_sidecar_cycle_run374 import _run, _setup

from ark.agency.audit import SQLiteActionAudit
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected,
    SyntheticMockCycleRejected,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)


def _cold_reopen(state):
    journal, ledger, audit, registry, call, links, token, path = state
    return (
        SyntheticPlanJournal(journal._path, journal._steps),
        SyntheticOccurrenceStore(ledger._path),
        SQLiteActionAudit(audit.path, clock_ms=lambda: 12),
        registry, call,
        SyntheticOccurrenceAuditLinkStore(links._path),
        token, path,
    )


@pytest.mark.parametrize(
    ("fault", "reservations", "audits", "links"),
    (
        ("after_running", 0, 0, 0),
        ("after_reservation", 1, 0, 0),
        ("after_pre_action_audit", 1, 1, 0),
        ("after_mock_marker", 1, 1, 1),
        ("after_audit_link", 1, 1, 1),
    ),
)
def test_cold_restart_preserves_unknown_and_all_cross_store_tips(
    tmp_path, fault, reservations, audits, links,
):
    state = _setup(tmp_path)
    initial = state[0].recover().tail
    with pytest.raises(SyntheticMockCrashInjected):
        _run(state, fault_at=fault)

    reopened = _cold_reopen(state)
    recovery = reopened[0].recover(retained=initial)
    assert recovery.step_statuses == (("root", "running", 1),)
    assert recovery.ambiguous_running_steps == ("root",)
    assert recovery.dispatch_authorized is False
    assert recovery.automatic_replay_authorized is False
    assert reopened[1].count_synthetic() == reservations
    assert len(reopened[2].events()) == audits
    assert reopened[5].read_witness().event_count == links
    assert [event.outcome for event in reopened[2].events()] == (
        ["synthetic_audit_before_mock"] if audits else []
    )

    # A new occurrence identifier must not bypass an unresolved plan state.
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _run(reopened, occurrence="different-after-restart")
    assert reopened[0].recover() == recovery
    assert reopened[1].count_synthetic() == reservations
    assert len(reopened[2].events()) == audits
    assert reopened[5].read_witness().event_count == links


def test_success_marker_is_not_replay_authority_after_reopen(tmp_path):
    state = _setup(tmp_path)
    receipt = _run(state)
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_known is False
    assert receipt.automatic_replay_authorized is False

    reopened = _cold_reopen(state)
    recovered = reopened[0].recover()
    assert recovered.step_statuses == (("root", "succeeded", 2),)
    assert recovered.ambiguous_running_steps == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert reopened[1].count_synthetic() == 1
    assert len(reopened[2].events()) == 1
    assert reopened[5].read_witness().event_count == 1

    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _run(reopened, occurrence="not-authorized")
    assert reopened[0].recover() == recovered
    assert reopened[1].count_synthetic() == 1
    assert len(reopened[2].events()) == 1
    assert reopened[5].read_witness().event_count == 1
