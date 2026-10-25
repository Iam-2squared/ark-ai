"""Revocation review must not return a witness rewritten after verification.

Everything is local, disconnected SQLite continuity evidence. A preserved
veto is not consent, privacy deletion or an authenticated external issuer.
"""

import pytest

import ark.personal_context_revocation_continuity_review as module
from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _store(tmp_path):
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    ledger.revoke(MemoryScope("owner", "notes"), at_ms=101)
    return ledger


def _equal_new(value):
    new = ("~" + value)[1:]
    assert new == value and new is not value
    return new


def _alter(witness, field):
    if field == "witness_id":
        object.__setattr__(witness, "witness_id", _equal_new(witness.witness_id))
    else:
        replaced = (witness.rows[0],)
        assert replaced == witness.rows and replaced is not witness.rows
        object.__setattr__(witness, "rows", replaced)


@pytest.mark.parametrize("field", ("witness_id", "rows"))
def test_final_integrity_callback_cannot_retarget_returned_witness(
    tmp_path, monkeypatch, field,
):
    ledger = _store(tmp_path)
    original = module.SyntheticRevocationWitness.assert_integrity

    def malicious_integrity(self):
        original(self)
        _alter(self, field)

    monkeypatch.setattr(
        module.SyntheticRevocationWitness, "assert_integrity", malicious_integrity,
    )
    with pytest.raises(
        SyntheticContextRevocationRejected,
        match="revocation result witness changed",
    ):
        module.review_revocation_continuity(ledger)


@pytest.mark.parametrize("field", ("witness_id", "rows"))
def test_commit_callback_cannot_retarget_returned_witness(
    tmp_path, monkeypatch, field,
):
    ledger = _store(tmp_path)
    original_connect = ledger._connect
    original_integrity = module.SyntheticRevocationWitness.assert_integrity
    captured = []

    def capture_integrity(self):
        original_integrity(self)
        captured.append(self)

    class Connection:
        def __init__(self, conn):
            self.conn = conn

        def __getattr__(self, attr):
            return getattr(self.conn, attr)

        def commit(self):
            self.conn.commit()
            assert len(captured) == 1
            _alter(captured[0], field)

        def close(self):
            self.conn.close()

    monkeypatch.setattr(
        module.SyntheticRevocationWitness, "assert_integrity", capture_integrity,
    )
    monkeypatch.setattr(
        ledger, "_connect", lambda *, readonly: Connection(original_connect(readonly=readonly)),
    )
    with pytest.raises(
        SyntheticContextRevocationRejected,
        match="revocation result witness changed",
    ):
        module.review_revocation_continuity(ledger)
    # The read-only connection committed its snapshot; no veto is removed.
    with monkeypatch.context() as undo:
        undo.setattr(ledger, "_connect", original_connect)
        undo.setattr(
            module.SyntheticRevocationWitness, "assert_integrity", original_integrity,
        )
        untouched = module.review_revocation_continuity(ledger)
    assert len(untouched.rows) == 1


def test_unmodified_veto_prefix_round_trips_without_authority(tmp_path):
    ledger = _store(tmp_path)
    first = module.review_revocation_continuity(ledger)
    second = module.review_revocation_continuity(ledger, retained=first)
    assert second == first
    assert len(second.rows) == 1
    assert second.witness_id.startswith("rvk_")
