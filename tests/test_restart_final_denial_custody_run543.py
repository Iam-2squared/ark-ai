"""Restart report callbacks cannot mutate retained tips or denial descriptors."""

from __future__ import annotations

import pytest

import ark.disconnected_restart_witness_bundle as restart
from ark.agency.disconnected_due_reservation import DisconnectedDueReservations
from ark.memory.disconnected_witness_ledger import (
    DisconnectedMemoryWitnessLedger,
    genesis_memory_ledger_witness,
)
from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger


def _fixture(tmp_path):
    memory = DisconnectedMemoryWitnessLedger(
        tmp_path / "memory.sqlite", create=True,
    )
    context = DisconnectedContextReplayLedger(
        tmp_path / "context.sqlite", create=True,
    )
    due = DisconnectedDueReservations(tmp_path / "due.sqlite")
    retained = (
        genesis_memory_ledger_witness(),
        context.witness(),
        due.witness(),
    )
    return (memory, context, due), retained


def _review(stores, retained):
    return restart.review_disconnected_restart_witnesses(
        stores[0], retained[0],
        stores[1], retained[1],
        stores[2], retained[2],
    )


_DENIALS = (
    "cross_store_atomicity_proven", "independent_custody_proven",
    "startup_authorized", "dispatch_authorized",
    "automatic_replay_authorized", "personal_context_use_authorized",
    "trusted_clock_verified",
)


@pytest.mark.parametrize("denial", _DENIALS)
def test_false_denial_callback_cannot_retarget_final_report(
    tmp_path, monkeypatch, denial,
):
    stores, retained = _fixture(tmp_path)

    def mutate(self):
        object.__setattr__(self, "fingerprint", "f" * 64)
        return False

    monkeypatch.setattr(
        restart.OfflineRestartWitnessReport,
        denial, property(mutate),
    )
    with pytest.raises(
        restart.OfflineRestartWitnessRejected,
        match="authority definition changed",
    ):
        _review(stores, retained)


def test_last_denial_callback_cannot_rewrite_earlier_denial(
    tmp_path, monkeypatch,
):
    stores, retained = _fixture(tmp_path)
    report_type = restart.OfflineRestartWitnessReport

    def mutate(self):
        monkeypatch.setattr(
            report_type, "startup_authorized",
            property(lambda other: True),
        )
        return False

    monkeypatch.setattr(report_type, "trusted_clock_verified", property(mutate))
    with pytest.raises(
        restart.OfflineRestartWitnessRejected,
        match="authority definition changed",
    ):
        _review(stores, retained)


def test_last_denial_callback_cannot_rewrite_retained_sqlite_tip(
    tmp_path, monkeypatch,
):
    stores, retained = _fixture(tmp_path)

    def mutate(self):
        object.__setattr__(retained[2], "fingerprint", "f" * 64)
        return False

    monkeypatch.setattr(
        restart.OfflineRestartWitnessReport,
        "trusted_clock_verified", property(mutate),
    )
    with pytest.raises(
        restart.OfflineRestartWitnessRejected,
        match="authority definition changed",
    ):
        _review(stores, retained)


def test_unmodified_restart_stays_non_authorizing(tmp_path):
    stores, retained = _fixture(tmp_path)
    report = _review(stores, retained)
    assert report.memory_epochs == 0
    assert report.context_requests == 0
    assert report.due_occurrences == 0
    assert all(getattr(report, name) is False for name in _DENIALS)
