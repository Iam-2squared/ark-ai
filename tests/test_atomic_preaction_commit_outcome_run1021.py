"""Run1021: atomic pre-action intent/audit COMMIT outcome is cold-read only.

Synthetic local SQLite only. This ledger never executes a tool or grants
dispatch, approval, trusted-clock, custody, or automatic replay authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(letter: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + letter * 64,
        "bound_" + "b" * 64,
        letter * 64,
    )


class _CommitBoundary:
    """Inject rollback-before-COMMIT or native-COMMIT/lost-acknowledgement."""

    def __init__(self, connection: sqlite3.Connection, *, durable: bool) -> None:
        self.connection = connection
        self.durable = durable
        self.commit_attempts = 0
        self.native_commits = 0
        self.rollbacks = 0

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            return self.connection.__exit__(exc_type, exc, traceback)
        self.commit_attempts += 1
        if self.durable:
            self.connection.__exit__(None, None, None)
            self.native_commits += 1
        else:
            self.connection.rollback()
            self.rollbacks += 1
        raise sqlite3.OperationalError(
            "synthetic pre-action COMMIT acknowledgement lost"
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
def test_atomic_intent_and_audit_pair_commit_outcome_requires_cold_readback(
    tmp_path, monkeypatch, durable: bool,
) -> None:
    path = tmp_path / "atomic-preaction-commit-outcome.sqlite3"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    first_claim = _claim("a")
    first = ledger.reserve(
        first_claim,
        retained=genesis_atomic_preaction_witness(),
    )
    second_claim = _claim("d")
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
            match="pre-action COMMIT acknowledgement lost",
        ):
            ledger.reserve(second_claim, retained=first)

    assert len(boundaries) == 1
    assert boundaries[0].commit_attempts == 1
    assert boundaries[0].native_commits == (1 if durable else 0)
    assert boundaries[0].rollbacks == (0 if durable else 1)

    cold = DisconnectedAtomicPreactionLedger(path)
    with sqlite3.connect(path) as connection:
        intents = connection.execute(
            "SELECT seq,occurrence_id FROM intents ORDER BY seq"
        ).fetchall()
        audits = connection.execute(
            "SELECT seq,occurrence_id FROM preaction_audit ORDER BY seq"
        ).fetchall()
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)

    if durable:
        assert intents == [
            (1, first_claim.occurrence_id),
            (2, second_claim.occurrence_id),
        ]
        assert audits == [
            (1, first_claim.occurrence_id),
            (2, second_claim.occurrence_id),
        ]
        with pytest.raises(AtomicPreactionRejected, match="stale"):
            cold.inspect(first)
        with sqlite3.connect(path) as connection:
            count, tip = connection.execute(
                "SELECT seq,chain_sha256 FROM intents ORDER BY seq DESC LIMIT 1"
            ).fetchone()
        observed = cold.inspect(AtomicPreactionWitness(count, tip))
        assert observed.occurrence_ids == (
            first_claim.occurrence_id,
            second_claim.occurrence_id,
        )
    else:
        assert intents == [(1, first_claim.occurrence_id)]
        assert audits == [(1, first_claim.occurrence_id)]
        observed = cold.inspect(first)
        assert observed.occurrence_ids == (first_claim.occurrence_id,)

    assert observed.tool_dispatch_authorized is False
    assert observed.automatic_replay_authorized is False
    assert observed.external_effect_proven is False
    assert not hasattr(cold, "execute")
