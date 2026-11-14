"""Synthetic due reservations reject substituted hash/JSON hooks before ledger access."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_due_reservation as due


@pytest.mark.parametrize("dependency", ("sha256", "dumps"))
@pytest.mark.parametrize("operation", ("create", "witness", "reserve"))
def test_due_digest_dependency_preaccess_denial(tmp_path, monkeypatch, dependency, operation):
    path = tmp_path / "due.sqlite3"
    ledger = due.DisconnectedDueReservations(path)
    origin = ledger.witness()
    unexpected: list[tuple[object, ...]] = []

    def untrusted(*args, **_kwargs):
        unexpected.append(args)
        raise AssertionError("substituted digest callback received due data")

    module = due.hashlib if dependency == "sha256" else due.json
    target = tmp_path / "new-due.sqlite3" if operation == "create" else path
    with monkeypatch.context() as patch:
        patch.setattr(module, dependency, untrusted)
        with pytest.raises(
            due.DueReservationRejected, match="due digest callback authority changed",
        ):
            if operation == "create":
                due.DisconnectedDueReservations(target)
            elif operation == "witness":
                ledger.witness()
            else:
                ledger.reserve_due(
                    policy_sha256="a" * 64,
                    due_at_ms=10,
                    observed_now_ms=11,
                    retained=origin,
                )
    assert unexpected == []
    assert not (tmp_path / "new-due.sqlite3").exists()
    assert ledger.witness() == origin


@pytest.mark.parametrize("dependency", ("sha256", "dumps"))
def test_genesis_due_digest_rejects_callback_replacement(tmp_path, monkeypatch, dependency):
    ledger = due.DisconnectedDueReservations(tmp_path / "due.sqlite3")
    before = ledger.witness()
    unexpected = []

    def untrusted(*_args, **_kwargs):
        unexpected.append(True)
        raise AssertionError("substituted genesis callback executed")

    module = due.hashlib if dependency == "sha256" else due.json
    with monkeypatch.context() as patch:
        patch.setattr(module, dependency, untrusted)
        with pytest.raises(
            due.DueReservationRejected, match="due digest callback authority changed",
        ):
            due.genesis_due_witness()
    assert unexpected == []
    assert ledger.witness() == before
