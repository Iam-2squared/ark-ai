"""Run546: a READ receipt recovery view is digest-only and non-authorizing."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_read_journal as mod

REQUEST = "req_" + "e" * 32
IN = "1" * 64
OUT = "2" * 64


def _receipt(index: int):
    return mod.ReadReceipt(
        REQUEST, "step_" + f"{index:016x}", "math.sum", IN, OUT,
    )


def _create_two(path):
    with mod.DisconnectedReadJournal.create(path) as journal:
        first = journal.append(_receipt(1), mod.genesis_witness())
        final = journal.append(_receipt(2), first)
    return final


def test_empty_recovery_has_genesis_and_no_permissions(tmp_path):
    path = tmp_path / "empty.sqlite"
    with mod.DisconnectedReadJournal.create(path) as journal:
        snapshot = journal.recover_receipts(mod.genesis_witness())
    assert type(snapshot) is mod.ReadJournalSnapshot
    assert snapshot.witness == mod.genesis_witness()
    assert snapshot.receipts == ()
    assert all(getattr(snapshot, flag) is False for flag in mod._SNAPSHOT_DENIALS)


def test_reopen_returns_ordered_digest_only_rows(tmp_path):
    path = tmp_path / "two.sqlite"
    retained = _create_two(path)
    with mod.DisconnectedReadJournal.open(path) as journal:
        snapshot = journal.recover_receipts(retained)
    assert snapshot.witness == retained
    assert snapshot.receipts == (_receipt(1), _receipt(2))
    assert tuple(row.step_id for row in snapshot.receipts) == (
        "step_0000000000000001", "step_0000000000000002",
    )
    assert all(row.input_digest == IN and row.result_digest == OUT
               for row in snapshot.receipts)
    assert all(getattr(snapshot, flag) is False for flag in mod._SNAPSHOT_DENIALS)


def test_recovery_rejects_stale_external_tip_without_rewriting(tmp_path):
    path = tmp_path / "stale.sqlite"
    retained = _create_two(path)
    with mod.DisconnectedReadJournal.open(path) as journal:
        with pytest.raises(mod.ReadJournalRejected, match="tip mismatch"):
            journal.recover_receipts(mod.genesis_witness())
        assert journal.verify(retained) == retained


def test_recovery_rejects_fake_authority_before_descriptor_access(monkeypatch, tmp_path):
    path = tmp_path / "authority.sqlite"
    retained = _create_two(path)
    calls = []

    def fake_authority(_self):
        calls.append(True)
        return True

    with mod.DisconnectedReadJournal.open(path) as journal:
        with monkeypatch.context() as patch:
            patch.setattr(
                mod.ReadJournalSnapshot, "effect_proven",
                property(fake_authority),
            )
            with pytest.raises(
                mod.ReadJournalRejected,
                match="gained authority|READ recovery result changed",
            ):
                journal.recover_receipts(retained)
        assert calls == []
        assert journal.verify(retained) == retained


def test_false_denial_descriptor_is_rejected_before_receipt_access(monkeypatch, tmp_path):
    path = tmp_path / "replacement.sqlite"
    retained = _create_two(path)
    calls = []

    def replace_tuple(self):
        calls.append(True)
        object.__setattr__(self, "receipts", tuple([*self.receipts]))
        return False

    with mod.DisconnectedReadJournal.open(path) as journal:
        with monkeypatch.context() as patch:
            patch.setattr(
                mod.ReadJournalSnapshot, "dispatch_authorized",
                property(replace_tuple),
            )
            with pytest.raises(mod.ReadJournalRejected, match="result changed"):
                journal.recover_receipts(retained)
        assert calls == []
        assert journal.verify(retained) == retained


def test_false_last_denial_descriptor_is_rejected_before_callback(monkeypatch, tmp_path):
    path = tmp_path / "descriptor.sqlite"
    retained = _create_two(path)
    calls = []

    def replace_descriptor(_self):
        calls.append(True)
        return False

    with mod.DisconnectedReadJournal.open(path) as journal:
        with monkeypatch.context() as patch:
            patch.setattr(
                mod.ReadJournalSnapshot, "independent_custody_proven",
                property(replace_descriptor),
            )
            with pytest.raises(mod.ReadJournalRejected, match="result changed"):
                journal.recover_receipts(retained)
        assert calls == []
        assert journal.verify(retained) == retained


@pytest.mark.parametrize("invalid", (
    mod.ReadJournalWitness(True, "a" * 64),
    mod.ReadJournalWitness(0, "not-a-sha"),
))
def test_recovery_requires_exact_bounded_retained_witness(tmp_path, invalid):
    path = tmp_path / "invalid.sqlite"
    with mod.DisconnectedReadJournal.create(path) as journal:
        with pytest.raises(mod.ReadJournalRejected):
            journal.recover_receipts(invalid)
        assert journal.verify(mod.genesis_witness()) == mod.genesis_witness()
