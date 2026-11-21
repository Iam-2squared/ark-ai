"""Quarantine ledger SQLite sidecar/ingress boundaries (disconnected only)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)

_POLICY = QuarantinePolicy("a" * 64, 0, 1000, 2, 0)
_SUFFIXES = ("-wal", "-shm", "-journal")


@pytest.mark.parametrize("suffix", _SUFFIXES)
def test_creation_refuses_orphan_regular_sidecar(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / "not-created.sqlite"
    orphan = path.with_name(path.name + suffix)
    orphan.write_bytes(b"untrusted orphan journal")
    with pytest.raises(ScheduleQuarantineRejected):
        DisconnectedScheduleQuarantineLedger(path, policy=_POLICY, create=True)
    assert not path.exists()
    assert orphan.read_bytes() == b"untrusted orphan journal"


@pytest.mark.parametrize("suffix", _SUFFIXES)
def test_existing_ledger_refuses_directory_sidecar_before_open(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(path, policy=_POLICY, create=True)
    retained = genesis_quarantine_witness(_POLICY)
    sidecar = path.with_name(path.name + suffix)
    sidecar.mkdir()
    with pytest.raises(ScheduleQuarantineRejected):
        ledger.inspect(retained=retained)
    with pytest.raises(ScheduleQuarantineRejected):
        ledger.quarantine_expired(
            index=0, occurrence_id=derive_quarantined_occurrence(_POLICY, 0),
            observed_ms=2000, retained=retained,
        )
    assert sidecar.is_dir()


@pytest.mark.parametrize("suffix", _SUFFIXES)
def test_existing_ledger_refuses_hardlinked_sidecar(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(path, policy=_POLICY, create=True)
    target = tmp_path / "unrelated.dat"
    target.write_bytes(b"unrelated private fixture")
    sidecar = path.with_name(path.name + suffix)
    try:
        os.link(target, sidecar)
    except OSError:
        pytest.skip("hard links unavailable on this fixture filesystem")
    with pytest.raises(ScheduleQuarantineRejected):
        ledger.inspect(retained=genesis_quarantine_witness(_POLICY))
    assert target.read_bytes() == b"unrelated private fixture"


def test_multiple_policy_rows_refused_without_accepting_any_policy(
    tmp_path: Path,
) -> None:
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(path, policy=_POLICY, create=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO policy VALUES (?,?,?,?,?)",
            ("b" * 64, 0, 1000, 2, 0),
        )
    with pytest.raises(ScheduleQuarantineRejected):
        ledger.inspect(retained=genesis_quarantine_witness(_POLICY))


@pytest.mark.parametrize("bad_sha", ["f" * 65, "f" * 65536])
def test_oversized_policy_label_rejected_before_store_open(
    tmp_path: Path, bad_sha: str,
) -> None:
    path = tmp_path / "never-created.sqlite"
    with pytest.raises(ScheduleQuarantineRejected):
        DisconnectedScheduleQuarantineLedger(
            path,
            policy=QuarantinePolicy(bad_sha, 0, 1000, 2, 0),
            create=True,
        )
    assert not path.exists()


def test_oversized_quarantine_occurrence_fails_without_a_write(
    tmp_path: Path,
) -> None:
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(path, policy=_POLICY, create=True)
    retained = genesis_quarantine_witness(_POLICY)
    with pytest.raises(ScheduleQuarantineRejected):
        ledger.quarantine_expired(
            index=0, occurrence_id="slot_" + "f" * 65536,
            observed_ms=2000, retained=retained,
        )
    assert ledger.inspect(retained=retained).count == 0


def test_oversized_persisted_chain_is_rejected_without_repair(
    tmp_path: Path,
) -> None:
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(path, policy=_POLICY, create=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO quarantines VALUES (?,?,?,?,?)",
            (1, derive_quarantined_occurrence(_POLICY, 0), 0, 2000, "f" * 65536),
        )
    with pytest.raises(ScheduleQuarantineRejected):
        ledger.inspect(retained=genesis_quarantine_witness(_POLICY))
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)
