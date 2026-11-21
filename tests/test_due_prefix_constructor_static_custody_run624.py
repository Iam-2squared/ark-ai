"""Synthetic due-prefix review must never run substituted authority code."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_due_prefix_review as due_prefix
from ark.agency.disconnected_due_reservation import DisconnectedDueReservations


def _fixture(tmp_path):
    ledger = DisconnectedDueReservations(tmp_path / "synthetic-due.sqlite")
    return ledger, ledger.witness()


def test_installed_report_constructor_refused_before_sqlite_open(tmp_path, monkeypatch):
    ledger, retained = _fixture(tmp_path)
    invoked = []

    def hostile(self, *args, **kwargs):
        invoked.append(True)
        raise AssertionError("hostile report initializer executed")

    with monkeypatch.context() as patch:
        patch.setattr(due_prefix.DisconnectedDuePrefixReview, "__init__", hostile)
        patch.setattr(
            ledger, "_open",
            lambda **_kwargs: pytest.fail("SQLite opened after constructor drift"),
        )
        with pytest.raises(
            due_prefix.DisconnectedDuePrefixRejected, match="authority definition changed",
        ):
            due_prefix.review_retained_due_prefix(ledger, retained)
    assert invoked == []


def test_forged_descriptor_get_not_invoked_by_original_identity_check(
    tmp_path, monkeypatch,
):
    ledger, retained = _fixture(tmp_path)
    invoked = []

    class HostileProperty:
        def __get__(self, instance, owner):
            invoked.append(True)
            raise AssertionError("descriptor getter executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            due_prefix.DisconnectedDuePrefixReview,
            "notification_authorized", HostileProperty(),
        )
        patch.setattr(
            ledger, "_open",
            lambda **_kwargs: pytest.fail("SQLite opened after authority drift"),
        )
        with pytest.raises(
            due_prefix.DisconnectedDuePrefixRejected, match="authority definition changed",
        ):
            due_prefix.review_retained_due_prefix(ledger, retained)
    assert invoked == []


def test_constructor_changed_during_retained_scan_never_executed(
    tmp_path, monkeypatch,
):
    ledger, retained = _fixture(tmp_path)
    original = due_prefix.due._inspect
    invoked = []

    def hostile(self, *args, **kwargs):
        invoked.append(True)
        raise AssertionError("hostile report initializer executed")

    def changed(conn):
        observed = original(conn)
        monkeypatch.setattr(due_prefix.DisconnectedDuePrefixReview, "__init__", hostile)
        return observed

    with monkeypatch.context() as patch:
        patch.setattr(due_prefix.due, "_inspect", changed)
        with pytest.raises(
            due_prefix.DisconnectedDuePrefixRejected, match="authority definition changed",
        ):
            due_prefix.review_retained_due_prefix(ledger, retained)
    assert invoked == []


def test_local_prefix_remains_passive_and_repeatable(tmp_path):
    ledger, retained = _fixture(tmp_path)
    one = due_prefix.review_retained_due_prefix(ledger, retained)
    two = due_prefix.review_retained_due_prefix(ledger, retained)
    assert one == two
    assert one.status == "UNCHANGED_LOCAL_HISTORY"
    assert one.previous_count == one.current_count == 0
    for flag in due_prefix._DENIAL_FLAGS:
        assert getattr(one, flag) is False
