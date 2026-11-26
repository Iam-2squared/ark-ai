"""Run1451: paired intent/audit reservation survives native-COMMIT hard exit.

Only synthetic local SQLite state is used. A recovered reservation grants no
dispatch, external-effect, trusted-approval, independent-custody or replay
authority.
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from pathlib import Path

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic


def _claim(letter: str) -> atomic.AtomicIntentClaim:
    return atomic.AtomicIntentClaim(
        "occ_" + letter * 64,
        "bound_" + letter * 64,
        letter * 64,
    )


def _hard_exit_after_native_reservation_commit(database: str) -> None:
    ledger = atomic.DisconnectedAtomicPreactionLedger(Path(database))
    native_open = ledger._open

    class ExitAfterCommit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def __enter__(self):
            self.connection.__enter__()
            return self

        def __exit__(self, exc_type, exc, traceback):
            result = self.connection.__exit__(exc_type, exc, traceback)
            if exc_type is None:
                # Both paired rows and the local chain tip are committed.
                # Exit before connection close or the witness can return.
                os._exit(79)
            return result

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    ledger._open = lambda *, read_only: (
        native_open(read_only=True)
        if read_only
        else ExitAfterCommit(native_open(read_only=False))
    )
    ledger.reserve(
        _claim("a"),
        retained=atomic.genesis_atomic_preaction_witness(),
    )
    os._exit(80)


def test_paired_preaction_reservation_survives_native_commit_hard_exit(
    tmp_path: Path,
) -> None:
    path = tmp_path / "preaction-native-commit-hard-exit.sqlite3"
    atomic.DisconnectedAtomicPreactionLedger.create(path)
    genesis = atomic.genesis_atomic_preaction_witness()

    process = multiprocessing.get_context("spawn").Process(
        target=_hard_exit_after_native_reservation_commit,
        args=(str(path),),
    )
    process.start()
    process.join(timeout=35)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        pytest.fail("pre-action native-COMMIT hard-exit fixture did not terminate")
    assert process.exitcode == 79

    cold = atomic.DisconnectedAtomicPreactionLedger(path)
    claim = _claim("a")
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        intents = connection.execute(
            "SELECT seq,occurrence_id,bound_action_id,request_sha256,chain_sha256 "
            "FROM intents ORDER BY seq"
        ).fetchall()
        audits = connection.execute(
            "SELECT seq,occurrence_id,audit_sha256 "
            "FROM preaction_audit ORDER BY seq"
        ).fetchall()

    assert len(intents) == len(audits) == 1
    assert intents[0][:4] == (
        1,
        claim.occurrence_id,
        claim.bound_action_id,
        claim.request_sha256,
    )
    assert audits[0][0:2] == (1, claim.occurrence_id)
    assert len(intents[0][4]) == 64
    assert len(audits[0][2]) == 64

    # The retained tip is derived from this same local ledger, so it is useful
    # only for consistency diagnosis, never as an independent replay witness.
    local_witness = atomic.AtomicPreactionWitness(1, intents[0][4])
    snapshot = cold.inspect(local_witness)
    assert snapshot.occurrence_ids == (claim.occurrence_id,)
    assert snapshot.witness == local_witness
    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.external_effect_proven is False
    assert snapshot.trusted_approval_verified is False
    assert snapshot.independent_custody_proven is False

    with pytest.raises(atomic.AtomicPreactionRejected):
        cold.inspect(genesis)
    with pytest.raises(atomic.AtomicPreactionRejected):
        cold.reserve(_claim("b"), retained=genesis)
    with pytest.raises(atomic.AtomicPreactionRejected):
        cold.reserve(claim, retained=local_witness)

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT seq,occurrence_id,bound_action_id,request_sha256,chain_sha256 "
            "FROM intents ORDER BY seq"
        ).fetchall() == intents
        assert connection.execute(
            "SELECT seq,occurrence_id,audit_sha256 "
            "FROM preaction_audit ORDER BY seq"
        ).fetchall() == audits
