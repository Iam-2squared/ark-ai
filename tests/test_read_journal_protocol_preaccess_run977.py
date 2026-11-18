"""Synthetic READ journal rejects replaced hash-chain rules before private access.

The SQLite fixtures hold only hashes, no actual tool results or tool dispatch.
Neither these tests nor local receipts establish consent, provenance or effects.
"""

from __future__ import annotations

import re

import pytest

import ark.agency.disconnected_read_journal as journal


def _receipt() -> journal.ReadReceipt:
    return journal.ReadReceipt(
        "req_" + "a" * 32,
        "step_" + "b" * 16,
        "math.sum",
        "c" * 64,
        "d" * 64,
    )


@pytest.mark.parametrize("dependency", ("sha256", "dumps"))
@pytest.mark.parametrize(
    "operation", ("create", "open", "verify", "recover", "append", "genesis"),
)
def test_substituted_codec_cannot_receive_private_read_receipts(
    tmp_path, monkeypatch, dependency: str, operation: str,
) -> None:
    path = tmp_path / "journal.sqlite"
    new_path = tmp_path / "new-journal.sqlite"
    unexpected: list[object] = []

    def untrusted(*args, **_kwargs):
        unexpected.extend(args)
        raise AssertionError("unreviewed digest callback saw READ journal input")

    with journal.DisconnectedReadJournal.create(path) as active:
        retained = journal.genesis_witness()
        codec = journal.hashlib if dependency == "sha256" else journal.json
        with monkeypatch.context() as patch:
            patch.setattr(codec, dependency, untrusted)
            with pytest.raises(
                journal.ReadJournalRejected,
                match="synthetic READ hash-chain protocol changed",
            ):
                if operation == "create":
                    journal.DisconnectedReadJournal.create(new_path)
                elif operation == "open":
                    journal.DisconnectedReadJournal.open(path)
                elif operation == "verify":
                    active.verify(retained)
                elif operation == "recover":
                    active.recover_receipts(retained)
                elif operation == "append":
                    active.append(_receipt(), retained)
                else:
                    journal.genesis_witness()
        assert active.verify(retained) == retained
    assert unexpected == []
    assert not new_path.exists()


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("_DOMAIN", b"forged-read-journal-domain"),
        ("_GENESIS", "0" * 64),
        ("_REQUEST", re.compile(r".*")),
        ("_OPS", frozenset(("unsafe.external.tool",))),
        ("_SCHEMA", "unreviewed.schema"),
        ("_MARKER_DDL", "CREATE TABLE marker (revision BLOB)"),
        ("_RECEIPT_DDL", "CREATE TABLE receipts (seq INTEGER)"),
        ("_MAX_ROWS", 129),
        ("_MAX_ROWS", 128.0),
    ),
)
def test_mutated_persisted_protocol_rejected_before_file_creation(
    tmp_path, monkeypatch, name: str, replacement: object,
) -> None:
    path = tmp_path / "not-created.sqlite"
    with monkeypatch.context() as patch:
        patch.setattr(journal, name, replacement)
        with pytest.raises(
            journal.ReadJournalRejected,
            match="synthetic READ hash-chain protocol changed",
        ):
            journal.DisconnectedReadJournal.create(path)
    assert not path.exists()


def test_unmodified_journal_read_recovery_and_append_remain_deny_only(tmp_path) -> None:
    path = tmp_path / "read.sqlite"
    with journal.DisconnectedReadJournal.create(path) as active:
        first = journal.genesis_witness()
        assert active.verify(first) == first
        next_tip = active.append(_receipt(), first)
        assert next_tip.count == 1
        assert active.verify(next_tip) == next_tip
        snapshot = active.recover_receipts(next_tip)
        assert snapshot.witness == next_tip
        assert snapshot.dispatch_authorized is False
        assert snapshot.effect_proven is False
        assert snapshot.automatic_replay_authorized is False
    with journal.DisconnectedReadJournal.open(path) as reopened:
        assert reopened.verify(next_tip) == next_tip
