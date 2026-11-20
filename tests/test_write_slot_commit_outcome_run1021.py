"""Run1021: multi-slot reservation is all-or-none at SQLite COMMIT.

Synthetic local WRITE-slot identities only. A reservation never executes a
ToolBackend and never proves authorization or exactly-once external effects.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


def _claim(letter: str) -> slots.DetachedWriteSlotClaim:
    plan = "plan_" + letter * 64
    step = "step_" + format(ord(letter), "016x")
    request = letter * 64
    return slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(plan, step, request),
        plan,
        step,
        request,
    )


class _CommitBoundary:
    """Inject failure before native COMMIT or after it succeeds."""

    def __init__(self, connection: sqlite3.Connection, *, durable: bool) -> None:
        self.connection = connection
        self.durable = durable
        self.commit_attempts = 0
        self.native_commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commit_attempts += 1
        if self.durable:
            self.connection.commit()
            self.native_commits += 1
        raise sqlite3.OperationalError(
            "synthetic write-slot COMMIT acknowledgement lost"
        )

    def rollback(self) -> None:
        self.rollbacks += 1
        self.connection.rollback()

    def close(self) -> None:
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


@pytest.mark.parametrize(
    "durable",
    (False, True),
    ids=("rollback-before-native-commit", "native-commit-ack-lost"),
)
def test_multi_slot_reservation_commit_outcome_is_all_or_none(
    tmp_path, monkeypatch, durable: bool,
) -> None:
    path = tmp_path / "write-slot-commit-outcome.sqlite3"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    claims = (_claim("a"), _claim("d"))
    genesis = slots.genesis_write_slot_witness()
    original_open = ledger._open
    boundaries: list[_CommitBoundary] = []

    def uncertain_open(*, read_only: bool):
        connection = original_open(read_only=read_only)
        if read_only:
            return connection
        boundary = _CommitBoundary(connection, durable=durable)
        boundaries.append(boundary)
        return boundary

    with monkeypatch.context() as patch:
        patch.setattr(ledger, "_open", uncertain_open)
        with pytest.raises(
            sqlite3.OperationalError,
            match="write-slot COMMIT acknowledgement lost",
        ):
            ledger.reserve_many(claims, retained=genesis)

    assert len(boundaries) == 1
    assert boundaries[0].commit_attempts == 1
    assert boundaries[0].native_commits == (1 if durable else 0)
    assert boundaries[0].rollbacks == 1

    cold = slots.DisconnectedWriteSlotLedger(path)
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT seq,slot_id,plan_id,step_id,request_sha256 "
            "FROM synthetic_write_slots ORDER BY seq"
        ).fetchall()
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)

    if durable:
        assert rows == [
            (1, claims[0].slot_id, claims[0].plan_id, claims[0].step_id,
             claims[0].request_sha256),
            (2, claims[1].slot_id, claims[1].plan_id, claims[1].step_id,
             claims[1].request_sha256),
        ]
        with pytest.raises(slots.WriteSlotLedgerRejected, match="stale"):
            cold.inspect(retained=genesis)
        with sqlite3.connect(path) as connection:
            count, tip = connection.execute(
                "SELECT seq,chain_sha256 FROM synthetic_write_slots "
                "ORDER BY seq DESC LIMIT 1"
            ).fetchone()
        observed = cold.inspect(
            retained=slots.WriteSlotLedgerWitness(count, tip),
        )
        with pytest.raises(slots.WriteSlotLedgerRejected, match="stale"):
            cold.reserve_many(claims, retained=genesis)
    else:
        assert rows == []
        observed = cold.inspect(retained=genesis)

    assert observed.count == (2 if durable else 0)
    assert observed.independently_authenticated is False
    assert not hasattr(cold, "execute")
