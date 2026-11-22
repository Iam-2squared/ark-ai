"""Run1020: a process exit after replay-ledger COMMIT leaves one denial-only row.

The child exits before returning a receipt. Parent recovery uses disposable
SQLite and synthetic context fixtures only; no disclosure or tool dispatch.
"""

from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path

import hashlib
import os
import sqlite3

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayRejected,
    genesis_offline_context_replay_witness,
)
from ark.personal_context_request_binding import bind_offline_context_request

_OWNER = "a" * 64
_SCOPE = "b" * 64
_RECORD = "rec_" + "c" * 32
_CONTENT = "synthetic private payload never stored in replay ledger"


def _binding(index: int):
    fixture = OfflineContextFixture(
        _RECORD,
        _OWNER,
        _SCOPE,
        _CONTENT,
        hashlib.sha256(_CONTENT.encode("utf-8")).hexdigest(),
        1000,
    )
    preview = build_offline_context_preview(
        (fixture,),
        owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,),
        observed_at_ms=100,
    )
    return bind_offline_context_request(
        "ctxreq_" + f"{index:064x}",
        preview,
    )


def _reserve_then_exit_after_native_commit(path: str) -> None:
    ledger = DisconnectedContextReplayLedger(Path(path))
    original_open = ledger._open

    class CommitThenExit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def commit(self) -> None:
            self.connection.commit()
            # Simulate process death after native COMMIT but before reserve()
            # can construct or return its local receipt.
            os._exit(47)

        def rollback(self) -> None:
            self.connection.rollback()

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name):
            return getattr(self.connection, name)

    ledger._open = lambda *, read_only=False: CommitThenExit(
        original_open(read_only=read_only),
    )
    ledger.reserve(
        _binding(1),
        retained=genesis_offline_context_replay_witness(),
    )
    os._exit(48)  # The injected commit boundary must always exit first.


def test_process_exit_after_commit_requires_readback_and_never_replays(
    tmp_path: Path,
) -> None:
    path = tmp_path / "personal-context-process-crash.sqlite3"
    initial = DisconnectedContextReplayLedger(path, create=True)
    genesis = initial.witness()
    assert genesis == genesis_offline_context_replay_witness()

    child = get_context("spawn").Process(
        target=_reserve_then_exit_after_native_commit,
        args=(str(path),),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 47, "child did not exit immediately after native COMMIT"

    # A fresh process/object can observe one hash-only reservation, but the
    # vanished child returned no receipt and the local witness grants no
    # consent, disclosure, dispatch, independent-custody or replay authority.
    cold = DisconnectedContextReplayLedger(path)
    observed = cold.witness()
    assert observed.count == 1
    assert observed.chain_sha256 != genesis.chain_sha256
    assert observed.independent_custody_proven is False

    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT seq,request_id,owner_digest,context_digest,binding_digest,chain_sha256 "
            "FROM context_requests ORDER BY seq",
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 1
        assert rows[0][1] == _binding(1).request_id
        assert all(type(value) is str and len(value) == 64 for value in rows[0][2:])
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)

    assert _CONTENT.encode("utf-8") not in path.read_bytes()
    with pytest.raises(OfflineContextReplayRejected, match="stale retained"):
        cold.reserve(_binding(2), retained=genesis)
    with pytest.raises(OfflineContextReplayRejected, match="duplicate"):
        cold.reserve(_binding(1), retained=observed)

    assert cold.witness() == observed
    assert cold.witness().count == 1
