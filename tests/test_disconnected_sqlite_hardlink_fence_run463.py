"""Hardlink-alias regression for three disconnected SQLite fixture ledgers.

These checks cannot eliminate TOCTOU or authenticate a filesystem. They
ensure an existing SQLite main-file alias cannot pass the normal path gate.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationRejected,
    genesis_due_witness,
)
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    genesis_witness,
)
from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
    genesis_privacy_veto_witness,
)


def _hardlink_alias(path: Path) -> Path:
    alias = path.with_name("alias-" + path.name)
    try:
        os.link(path, alias)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"hardlink fixture not supported: {exc}")
    if path.stat().st_nlink != 2 or alias.stat().st_nlink != 2:
        alias.unlink()
        pytest.skip("filesystem does not expose two hardlink references")
    return alias


@pytest.mark.parametrize("via_alias", [False, True])
def test_privacy_veto_hardlink_refused_then_original_recovers(
    tmp_path: Path, via_alias: bool,
) -> None:
    path = tmp_path / "veto.db"
    ledger = DisconnectedPrivacyVetoLedger(path)
    assert ledger.witness() == genesis_privacy_veto_witness()
    alias = _hardlink_alias(path)
    try:
        with pytest.raises(OfflinePrivacyVetoRejected, match="regular-file link"):
            if via_alias:
                DisconnectedPrivacyVetoLedger(alias)
            else:
                ledger.witness()
    finally:
        alias.unlink()
    assert ledger.witness() == genesis_privacy_veto_witness()


@pytest.mark.parametrize("via_alias", [False, True])
def test_due_reservation_hardlink_refused_then_original_recovers(
    tmp_path: Path, via_alias: bool,
) -> None:
    path = tmp_path / "due.db"
    ledger = DisconnectedDueReservations(path)
    assert ledger.witness() == genesis_due_witness()
    alias = _hardlink_alias(path)
    try:
        with pytest.raises(DueReservationRejected, match="regular-file link"):
            if via_alias:
                DisconnectedDueReservations(alias)
            else:
                ledger.witness()
    finally:
        alias.unlink()
    assert ledger.witness() == genesis_due_witness()


@pytest.mark.parametrize("via_alias", [False, True])
def test_read_journal_hardlink_refused_then_original_recovers(
    tmp_path: Path, via_alias: bool,
) -> None:
    path = tmp_path / "read.db"
    with DisconnectedReadJournal.create(path) as journal:
        assert journal.verify(genesis_witness()) == genesis_witness()
    alias = _hardlink_alias(path)
    try:
        with pytest.raises(ReadJournalRejected, match="regular-file link"):
            DisconnectedReadJournal.open(alias if via_alias else path)
    finally:
        alias.unlink()
    with DisconnectedReadJournal.open(path) as journal:
        assert journal.verify(genesis_witness()) == genesis_witness()
