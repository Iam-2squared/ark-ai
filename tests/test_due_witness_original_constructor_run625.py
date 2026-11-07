"""Synthetic due witness construction must not invoke a forged initializer.

The SQLite reservation fixture cannot authenticate a scheduler clock, grant
notification dispatch, or turn an ambiguous COMMIT into a replay instruction.
"""

import pytest

import ark.agency.disconnected_due_reservation as due


def _hostile_initializer(calls):
    def hostile(self, *args, **kwargs):
        calls.append("initializer")
        raise AssertionError("forged due witness initializer executed")
    return hostile


def test_genesis_rejects_installed_initializer_without_execution(monkeypatch):
    calls = []
    with monkeypatch.context() as patch:
        patch.setattr(
            due.DueReservationWitness, "__init__", _hostile_initializer(calls),
        )
        with pytest.raises(due.DueReservationRejected, match="witness authority"):
            due.genesis_due_witness()
    assert calls == []
    assert due.genesis_due_witness().count == 0


def test_reservation_rejects_initializer_before_opening_sqlite(tmp_path, monkeypatch):
    ledger = due.DisconnectedDueReservations(tmp_path / "due.sqlite")
    retained = ledger.witness()
    calls = []
    with monkeypatch.context() as patch:
        patch.setattr(
            due.DueReservationWitness, "__init__", _hostile_initializer(calls),
        )
        patch.setattr(
            ledger, "_open", lambda **kwargs: pytest.fail("unexpected ledger I/O"),
        )
        with pytest.raises(due.DueReservationRejected, match="witness authority"):
            ledger.reserve_due(
                policy_sha256="a" * 64,
                due_at_ms=100, observed_now_ms=100,
                retained=retained,
            )
    assert calls == []
    assert ledger.witness() == retained


def test_constructor_swap_in_digest_callback_denied_before_invocation(monkeypatch):
    calls = []
    original_digest = due._digest

    with monkeypatch.context() as patch:
        def drift(rows):
            result = original_digest(rows)
            patch.setattr(
                due.DueReservationWitness, "__init__", _hostile_initializer(calls),
            )
            return result

        patch.setattr(due, "_digest", drift)
        with pytest.raises(due.DueReservationRejected, match="witness authority"):
            due.genesis_due_witness()
    assert calls == []


def test_readonly_witness_rejects_constructor_swap_after_sqlite_scan(
    tmp_path, monkeypatch,
):
    ledger = due.DisconnectedDueReservations(tmp_path / "due.sqlite")
    baseline = ledger.witness()
    calls = []
    original_inspect = due._inspect

    with monkeypatch.context() as patch:
        def drift(conn):
            result = original_inspect(conn)
            patch.setattr(
                due.DueReservationWitness, "__init__", _hostile_initializer(calls),
            )
            return result

        patch.setattr(due, "_inspect", drift)
        with pytest.raises(due.DueReservationRejected, match="witness authority"):
            ledger.witness()
    assert calls == []
    assert ledger.witness() == baseline
