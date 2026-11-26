"""Detached READ journal append must use exact CAS fields, never patched equality.

Synthetic SQLite receipts are not ToolBackend dispatch, provenance, human
consent, trusted time, or permission to replay a potentially ambiguous write.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadJournalWitness,
    ReadReceipt,
    genesis_witness,
)


def _receipt(step):
    return ReadReceipt(
        "req_" + "a" * 32,
        "step_" + f"{step:016x}",
        "math.sum",
        "b" * 64,
        "c" * 64,
    )


@pytest.mark.parametrize("forgery", (
    "stale_genesis",
    "wrong_hash",
    "wrong_count",
))
def test_patched_witness_equality_cannot_bypass_append_cas(
    tmp_path, monkeypatch, forgery,
):
    with DisconnectedReadJournal.create(tmp_path / "read-cas.sqlite") as journal:
        initial = genesis_witness()
        committed = journal.append(_receipt(1), initial)
        monkeypatch.setattr(ReadJournalWitness, "__eq__", lambda self, other: True)
        rejected = {
            "stale_genesis": initial,
            "wrong_hash": ReadJournalWitness(1, "f" * 64),
            "wrong_count": ReadJournalWitness(0, committed.tip_sha256),
        }[forgery]
        with pytest.raises(ReadJournalRejected, match="stale"):
            journal.append(_receipt(2), rejected)
        observed = journal.verify(committed)
        assert observed.count == 1
        assert observed.tip_sha256 == committed.tip_sha256
        assert observed.dispatch_authorized is False
        assert observed.replay_authorized is False


def test_valid_append_still_succeeds_when_equality_is_patched(tmp_path, monkeypatch):
    with DisconnectedReadJournal.create(tmp_path / "valid-read-cas.sqlite") as journal:
        first = journal.append(_receipt(1), genesis_witness())
        monkeypatch.setattr(ReadJournalWitness, "__eq__", lambda self, other: False)
        next_witness = journal.append(_receipt(2), first)
        assert next_witness.count == 2
        assert next_witness.tip_sha256 != first.tip_sha256
        assert next_witness.dispatch_authorized is False
        assert next_witness.replay_authorized is False


def test_unmodified_cas_does_not_authorize_real_action(tmp_path):
    with DisconnectedReadJournal.create(tmp_path / "original-read-cas.sqlite") as journal:
        first = journal.append(_receipt(1), genesis_witness())
        assert first.count == 1
        assert first.dispatch_authorized is False
        assert first.effect_proven is False
        assert first.independent_custody_proven is False
