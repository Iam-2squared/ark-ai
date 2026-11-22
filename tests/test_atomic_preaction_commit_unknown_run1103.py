"""Run1103: atomic intent/audit commit ambiguity after cold restart."""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic


class _CommitBoundary:
    """Lose the local acknowledgement immediately before/after native COMMIT."""

    def __init__(self, connection: sqlite3.Connection, *, durable: bool) -> None:
        self.connection = connection
        self.durable = durable

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            self.connection.rollback()
            return False
        if self.durable:
            self.connection.commit()
        else:
            self.connection.rollback()
        raise sqlite3.OperationalError(
            "atomic pre-action COMMIT acknowledgement lost"
        )

    def close(self) -> None:
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


def _claim() -> atomic.AtomicIntentClaim:
    return atomic.AtomicIntentClaim(
        "occ_" + "a" * 64,
        "bound_" + "b" * 64,
        "c" * 64,
    )


@pytest.mark.parametrize("durable", (False, True))
def test_atomic_preaction_commit_unknown_requires_cold_readback(
    tmp_path, monkeypatch, durable: bool,
) -> None:
    path = tmp_path / "atomic-preaction-commit-unknown.sqlite3"
    ledger = atomic.DisconnectedAtomicPreactionLedger.create(path)
    genesis = atomic.genesis_atomic_preaction_witness()
    claim = _claim()
    expected_tip = atomic._chain(genesis.tip_sha256, 1, claim)
    expected = atomic.AtomicPreactionWitness(1, expected_tip)
    original_open = ledger._open

    def uncertain_open(*, read_only: bool):
        connection = original_open(read_only=read_only)
        if read_only:
            return connection
        return _CommitBoundary(connection, durable=durable)

    monkeypatch.setattr(ledger, "_open", uncertain_open)
    with pytest.raises(
        sqlite3.OperationalError,
        match="atomic pre-action COMMIT acknowledgement lost",
    ):
        ledger.reserve(claim, retained=genesis)

    # A lost acknowledgement is never retried against the same handle.
    # Cold recovery determines whether the paired rows committed together.
    cold = atomic.DisconnectedAtomicPreactionLedger(path)
    if durable:
        snapshot = cold.inspect(expected)
        assert snapshot.occurrence_ids == (claim.occurrence_id,)
        assert snapshot.witness == expected
        with pytest.raises(atomic.AtomicPreactionRejected):
            cold.inspect(genesis)
        expected_count = 1
    else:
        snapshot = cold.inspect(genesis)
        assert snapshot.occurrence_ids == ()
        assert snapshot.witness == genesis
        with pytest.raises(atomic.AtomicPreactionRejected):
            cold.inspect(expected)
        expected_count = 0

    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.external_effect_proven is False
    assert snapshot.trusted_approval_verified is False
    assert snapshot.independent_custody_proven is False

    with sqlite3.connect(path) as connection:
        intents = connection.execute(
            "SELECT seq,occurrence_id,bound_action_id,request_sha256 "
            "FROM intents ORDER BY seq"
        ).fetchall()
        audits = connection.execute(
            "SELECT seq,occurrence_id FROM preaction_audit ORDER BY seq"
        ).fetchall()
    assert len(intents) == len(audits) == expected_count
    if durable:
        assert intents == [(
            1, claim.occurrence_id, claim.bound_action_id, claim.request_sha256,
        )]
        assert audits == [(1, claim.occurrence_id)]
    else:
        assert intents == audits == []
