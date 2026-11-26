"""READ journal authority descriptors remain the original deny-only definitions.

The local SQLite journal stores synthetic digests, never a real tool effect.
Post-COMMIT rejection is diagnostic, not evidence that the append rolled back.
"""

import pytest

import ark.agency.disconnected_read_journal as read


def _receipt():
    return read.ReadReceipt(
        "req_" + "a" * 32, "step_" + "b" * 16, "math.sum",
        "c" * 64, "d" * 64,
    )


@pytest.mark.parametrize("name", read._WITNESS_DENIALS)
def test_equal_false_retained_witness_descriptor_cannot_validate(tmp_path, monkeypatch, name):
    with read.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        retained = read.genesis_witness()
        with monkeypatch.context() as patch:
            patch.setattr(read.ReadJournalWitness, name, property(lambda _: False))
            with pytest.raises(read.ReadJournalRejected, match="invalid retained witness"):
                journal.append(_receipt(), retained)
        assert journal.verify(read.genesis_witness()).count == 0


@pytest.mark.parametrize("name", read._SNAPSHOT_DENIALS)
def test_equal_false_snapshot_descriptor_rejected_after_read_only_commit(
    tmp_path, monkeypatch, name,
):
    with read.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        tip = journal.append(_receipt(), read.genesis_witness())
        with monkeypatch.context() as patch:
            patch.setattr(read.ReadJournalSnapshot, name, property(lambda _: False))
            with pytest.raises(read.ReadJournalRejected, match="READ recovery result changed"):
                journal.recover_receipts(tip)
        assert journal.verify(tip) == tip


def test_late_witness_getter_cannot_replace_an_earlier_denial(tmp_path, monkeypatch):
    with read.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        receipt_type = read.ReadJournalWitness
        original = receipt_type.__getattribute__

        def getter(self, name):
            value = original(self, name)
            if name == "independent_custody_proven":
                monkeypatch.setattr(
                    receipt_type, "dispatch_authorized", property(lambda _: False),
                )
            return value

        with monkeypatch.context() as patch:
            patch.setattr(receipt_type, "__getattribute__", getter)
            with pytest.raises(read.ReadJournalRejected, match="invalid retained witness"):
                journal.verify(read.genesis_witness())


def test_late_snapshot_getter_cannot_replace_an_earlier_denial(tmp_path, monkeypatch):
    with read.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        tip = journal.append(_receipt(), read.genesis_witness())
        snapshot_type = read.ReadJournalSnapshot
        original = snapshot_type.__getattribute__

        def getter(self, name):
            value = original(self, name)
            if name == "independent_custody_proven":
                monkeypatch.setattr(
                    snapshot_type, "dispatch_authorized", property(lambda _: False),
                )
            return value

        with monkeypatch.context() as patch:
            patch.setattr(snapshot_type, "__getattribute__", getter)
            with pytest.raises(read.ReadJournalRejected, match="READ recovery result changed"):
                journal.recover_receipts(tip)
        assert journal.verify(tip) == tip


@pytest.mark.parametrize("name", read._WITNESS_DENIALS)
def test_preinstalled_witness_factory_cannot_claim_append_success(
    tmp_path, monkeypatch, name,
):
    with read.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        original_type = read.ReadJournalWitness
        retained = read.genesis_witness()
        factory_calls = []

        def factory(count, tip):
            factory_calls.append(True)
            if count == 1:
                monkeypatch.setattr(
                    original_type, name, property(lambda _: False),
                )
            return original_type(count, tip)

        with monkeypatch.context() as patch:
            patch.setattr(read, "ReadJournalWitness", factory)
            with pytest.raises(
                read.ReadJournalRejected,
                match="synthetic READ carrier class changed",
            ):
                journal.append(_receipt(), retained)
        # A substituted factory must be rejected before any SQLite append.
        assert factory_calls == []
        assert journal._scan().count == 0


def test_unmodified_read_journal_recovers_without_dispatch(tmp_path):
    with read.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        tip = journal.append(_receipt(), read.genesis_witness())
        snap = journal.recover_receipts(tip)
        assert snap.witness == tip
        assert len(snap.receipts) == 1
        for flag in read._SNAPSHOT_DENIALS:
            assert getattr(snap, flag) is False
