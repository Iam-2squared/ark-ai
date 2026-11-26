"""Quarantine ledger's synthetic hash-chain admission fails closed.

Disposable SQLite only. There is no trusted clock, notification, consent,
real ToolBackend, or authorization to retry a quarantined occurrence.
"""

from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import pytest

from ark import disconnected_schedule_quarantine_ledger as quarantine


def _fixture(tmp_path):
    policy = quarantine.QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "quarantine.sqlite"
    ledger = quarantine.DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    witness = quarantine.genesis_quarantine_witness(policy)
    occurrence = quarantine.derive_quarantined_occurrence(policy, 0)
    return ledger, policy, path, witness, occurrence


@pytest.mark.parametrize(
    "mutation",
    ("hashlib", "json", "domain", "sha_pattern", "slot_pattern", "ddl", "row_limit"),
)
def test_protocol_mutation_refused_before_sqlite_writer_open(
    tmp_path, monkeypatch, mutation,
):
    ledger, _policy, path, witness, occurrence = _fixture(tmp_path)
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append(True)
        raise AssertionError("substituted codec or SQLite writer was called")

    def mutate(patch):
        if mutation == "hashlib":
            patch.setattr(quarantine, "hashlib", SimpleNamespace(sha256=forbidden))
        elif mutation == "json":
            patch.setattr(quarantine, "json", SimpleNamespace(dumps=forbidden))
        elif mutation == "domain":
            patch.setattr(quarantine, "_DOMAIN", b"changed-hash-chain-domain")
        elif mutation == "sha_pattern":
            patch.setattr(quarantine, "_SHA", quarantine.re.compile(r".*"))
        elif mutation == "slot_pattern":
            patch.setattr(quarantine, "_SLOT", quarantine.re.compile(r".*"))
        elif mutation == "ddl":
            patch.setattr(quarantine, "_DDL", tuple(list(quarantine._DDL)))
        else:
            patch.setattr(quarantine, "_MAX_ROWS", 513)

    with monkeypatch.context() as patch:
        patch.setattr(ledger, "_open", forbidden)
        mutate(patch)
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected, match="digest or protocol changed",
        ):
            ledger.quarantine_expired(
                index=0, occurrence_id=occurrence, observed_ms=10_501,
                retained=witness,
            )
    assert attempted == []
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (0,)


@pytest.mark.parametrize("mutation", ("hashlib", "json", "domain"))
def test_genesis_and_occurrence_refuse_tampered_protocol(
    tmp_path, monkeypatch, mutation,
):
    _ledger, policy, _path, _witness, _occurrence = _fixture(tmp_path)
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append(True)
        raise AssertionError("untrusted digest callback invoked")

    with monkeypatch.context() as patch:
        if mutation == "hashlib":
            patch.setattr(quarantine, "hashlib", SimpleNamespace(sha256=forbidden))
        elif mutation == "json":
            patch.setattr(quarantine, "json", SimpleNamespace(dumps=forbidden))
        else:
            patch.setattr(quarantine, "_DOMAIN", b"changed-hash-chain-domain")
        for operation in (
            lambda: quarantine.genesis_quarantine_witness(policy),
            lambda: quarantine.derive_quarantined_occurrence(policy, 0),
        ):
            with pytest.raises(
                quarantine.ScheduleQuarantineRejected,
                match="digest or protocol changed",
            ):
                operation()
    assert attempted == []


def test_restored_protocol_restarts_with_denial_only_receipt(tmp_path):
    ledger, policy, path, prior, occurrence = _fixture(tmp_path)
    receipt = ledger.quarantine_expired(
        index=0, occurrence_id=occurrence, observed_ms=10_501,
        retained=prior,
    )
    assert receipt.witness.count == 1
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    assert receipt.consent_verified is False
    reopened = quarantine.DisconnectedScheduleQuarantineLedger(
        path, policy=policy,
    )
    assert reopened.inspect(retained=receipt.witness) == receipt.witness
