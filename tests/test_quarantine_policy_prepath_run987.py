"""Synthetic quarantine policies fail before any local filesystem or SQLite work."""

import sqlite3
from pathlib import Path

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    genesis_quarantine_witness,
)


@pytest.mark.parametrize(
    "policy",
    (
        QuarantinePolicy("bad", 1_000, 1_000, 1, 0),
        QuarantinePolicy("a" * 64, -1, 1_000, 1, 0),
        QuarantinePolicy("a" * 64, 2**63 - 1, 1_000, 1, 0),
        QuarantinePolicy("a" * 64, 1_000, 1_000, 1, 1_000),
    ),
)
def test_invalid_policy_rejected_before_filesystem_or_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch, policy: QuarantinePolicy,
) -> None:
    path = tmp_path / "synthetic-quarantine.sqlite3"

    def deny_io(*_args, **_kwargs):
        raise AssertionError("invalid policy reached filesystem or SQLite")

    monkeypatch.setattr(Path, "lstat", deny_io)
    monkeypatch.setattr(sqlite3, "connect", deny_io)

    with pytest.raises(ScheduleQuarantineRejected, match="invalid bounded synthetic schedule"):
        DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)


def test_valid_policy_still_supports_readonly_restart(tmp_path) -> None:
    path = tmp_path / "synthetic-quarantine.sqlite3"
    policy = QuarantinePolicy("b" * 64, 1_000, 1_000, 2, 100)
    DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    restarted = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    witness = genesis_quarantine_witness(policy)
    assert restarted.inspect(retained=witness) == witness
    assert witness.independently_authenticated is False
