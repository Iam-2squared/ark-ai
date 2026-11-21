"""Original scheduler prefix authority is pinned before read-only SQLite I/O.

No trusted time, independent witness custody, actual notification, dispatch,
consent, or replay authority can follow from these synthetic checks.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_due_prefix_review as prefix
from ark.agency.disconnected_due_reservation import DisconnectedDueReservations


def _case(tmp_path):
    ledger = DisconnectedDueReservations(tmp_path / "only-synthetic-due.sqlite")
    return ledger, ledger.witness()


@pytest.mark.parametrize("flag", prefix._DENIAL_FLAGS)
def test_preinstalled_false_only_denial_is_rejected_before_disk_read(
    tmp_path, monkeypatch, flag,
):
    ledger, retained = _case(tmp_path)
    invoked = []
    opened = []

    def fake_denial(self):
        invoked.append(flag)
        return False

    def block_read(*args, **kwargs):
        opened.append(True)
        raise AssertionError("SQLite should not be opened for a forged authority")

    with monkeypatch.context() as patch:
        patch.setattr(prefix.DisconnectedDuePrefixReview, flag,
                      property(fake_denial))
        patch.setattr(ledger, "_open", block_read)
        with pytest.raises(prefix.DisconnectedDuePrefixRejected,
                           match="authority definition changed"):
            prefix.review_retained_due_prefix(ledger, retained)
    assert invoked == []
    assert opened == []


def test_false_only_retained_witness_authority_is_rejected_before_disk(
    tmp_path, monkeypatch,
):
    ledger, retained = _case(tmp_path)
    invoked = []
    opened = []

    def fake_denial(self):
        invoked.append(True)
        return False

    def block_read(*args, **kwargs):
        opened.append(True)
        raise AssertionError("no SQLite read is permitted")

    with monkeypatch.context() as patch:
        patch.setattr(prefix._WITNESS, "independent_custody_proven",
                      property(fake_denial))
        patch.setattr(ledger, "_open", block_read)
        with pytest.raises(prefix.DisconnectedDuePrefixRejected,
                           match="authority definition changed"):
            prefix.review_retained_due_prefix(ledger, retained)
    assert invoked == []
    assert opened == []


def test_denial_replaced_after_snapshot_cannot_escape(tmp_path, monkeypatch):
    ledger, retained = _case(tmp_path)
    original = prefix.due._inspect
    invoked = []

    def change_after_snapshot(conn):
        report = original(conn)
        monkeypatch.setattr(
            prefix.DisconnectedDuePrefixReview,
            "automatic_replay_authorized",
            property(lambda self: invoked.append(True) or False),
        )
        return report

    with monkeypatch.context() as patch:
        patch.setattr(prefix.due, "_inspect", change_after_snapshot)
        with pytest.raises(prefix.DisconnectedDuePrefixRejected,
                           match="authority definition changed"):
            prefix.review_retained_due_prefix(ledger, retained)
    assert invoked == []


def test_intact_prefix_reports_no_authorization(tmp_path):
    ledger, retained = _case(tmp_path)
    review = prefix.review_retained_due_prefix(ledger, retained)
    assert review.status == "UNCHANGED_LOCAL_HISTORY"
    assert review.previous_count == review.current_count == 0
    assert all(getattr(review, name) is False for name in prefix._DENIAL_FLAGS)
    assert ledger.witness() == retained
