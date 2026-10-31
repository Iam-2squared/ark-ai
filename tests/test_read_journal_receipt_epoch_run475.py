"""SQLite READ journal must preserve caller epochs and deny forged post-COMMIT receipts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.agency.disconnected_read_journal as journal_module

REQUEST = "req_" + "a" * 32
STEP = "step_" + "1" * 16
DIGEST = "b" * 64


def _receipt():
    return journal_module.ReadReceipt(
        REQUEST, STEP, "math.sum", DIGEST, "c" * 64,
    )


def _journal(tmp_path):
    return journal_module.DisconnectedReadJournal.create(tmp_path / "read-journal.db")


def test_valid_journal_restart_keeps_non_authorizing_retained_tip(tmp_path):
    with _journal(tmp_path) as journal:
        genesis = journal_module.genesis_witness()
        tip = journal.append(_receipt(), genesis)
        assert journal.verify(tip) == tip
        assert tip.dispatch_authorized is False
        assert tip.effect_proven is False
        assert tip.replay_authorized is False
    with journal_module.DisconnectedReadJournal.open(tmp_path / "read-journal.db") as j:
        assert j.verify(tip) == tip


@pytest.mark.parametrize("equal_value", [False, True])
def test_append_receipt_changed_during_hash_rolls_back(tmp_path, monkeypatch, equal_value):
    with _journal(tmp_path) as journal:
        genesis = journal_module.genesis_witness()
        row = _receipt()
        original = journal_module._chain

        def mutate(previous, index, receipt):
            current = row.result_digest
            replacement = (
                current.encode("ascii").decode("ascii")
                if equal_value else "e" * 64
            )
            assert replacement is not current
            object.__setattr__(row, "result_digest", replacement)
            return original(previous, index, receipt)

        with monkeypatch.context() as patch:
            patch.setattr(journal_module, "_chain", mutate)
            with pytest.raises(journal_module.ReadJournalRejected, match="carriers changed"):
                journal.append(row, genesis)
        assert journal.verify(genesis) == genesis


def test_append_retained_witness_changed_during_hash_rolls_back(tmp_path, monkeypatch):
    with _journal(tmp_path) as journal:
        genesis = journal_module.genesis_witness()
        original = journal_module._chain

        def mutate(previous, index, row):
            object.__setattr__(genesis, "tip_sha256", "f" * 64)
            return original(previous, index, row)

        with monkeypatch.context() as patch:
            patch.setattr(journal_module, "_chain", mutate)
            with pytest.raises(journal_module.ReadJournalRejected, match="carriers changed"):
                journal.append(_receipt(), genesis)
        assert journal.verify(journal_module.genesis_witness()).count == 0


def test_verify_rejects_witness_replacement_during_scan(tmp_path, monkeypatch):
    with _journal(tmp_path) as journal:
        genesis = journal_module.genesis_witness()
        original = journal._scan

        def mutate():
            object.__setattr__(
                genesis, "tip_sha256", genesis.tip_sha256.encode().decode(),
            )
            return original()

        with monkeypatch.context() as patch:
            patch.setattr(journal, "_scan", mutate)
            with pytest.raises(journal_module.ReadJournalRejected, match="retained"):
                journal.verify(genesis)
        assert journal.verify(journal_module.genesis_witness()).count == 0


def test_verify_rejects_forged_scan_receipt(tmp_path, monkeypatch):
    with _journal(tmp_path) as journal:
        genesis = journal_module.genesis_witness()
        with monkeypatch.context() as patch:
            patch.setattr(journal, "_scan", lambda: SimpleNamespace(
                count=genesis.count, tip_sha256=genesis.tip_sha256,
                dispatch_authorized=True,
            ))
            with pytest.raises(journal_module.ReadJournalRejected, match="external witness"):
                journal.verify(genesis)
        assert journal.verify(genesis) == genesis


def test_forged_witness_factory_after_commit_is_rejected_without_retry(
    tmp_path, monkeypatch,
):
    with _journal(tmp_path) as journal:
        genesis = journal_module.genesis_witness()
        original = journal_module.ReadJournalWitness

        def forge(count, digest):
            if count == 1:
                return SimpleNamespace(
                    count=count, tip_sha256=digest,
                    dispatch_authorized=True, effect_proven=True,
                )
            return original(count, digest)

        with monkeypatch.context() as patch:
            patch.setattr(journal_module, "ReadJournalWitness", forge)
            with pytest.raises(journal_module.ReadJournalRejected, match="post-commit"):
                journal.append(_receipt(), genesis)
        # The error was observed AFTER COMMIT. Never report rollback or re-append.
        committed = journal._scan()
        assert committed.count == 1
        assert journal.verify(committed) == committed
        with pytest.raises(journal_module.ReadJournalRejected):
            journal.append(_receipt(), committed)


def test_postcommit_witness_callback_mutation_is_reported(tmp_path, monkeypatch):
    with _journal(tmp_path) as journal:
        genesis = journal_module.genesis_witness()
        original = journal_module.ReadJournalWitness

        def change_then_construct(count, digest):
            if count == 1:
                old = genesis.tip_sha256
                replacement = old.encode("ascii").decode("ascii")
                assert replacement is not old
                object.__setattr__(genesis, "tip_sha256", replacement)
            return original(count, digest)

        with monkeypatch.context() as patch:
            patch.setattr(journal_module, "ReadJournalWitness", change_then_construct)
            with pytest.raises(journal_module.ReadJournalRejected, match="carriers changed"):
                journal.append(_receipt(), genesis)
        assert journal._scan().count == 1
