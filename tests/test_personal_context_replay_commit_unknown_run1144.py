"""Run1144: Personal Context replay reservation COMMIT acknowledgement loss."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayRejected,
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


@pytest.mark.parametrize("durable", (False, True), ids=("rolled-back", "committed"))
def test_reservation_commit_ack_loss_is_resolved_by_cold_readback(
    tmp_path: Path,
    durable: bool,
) -> None:
    path = tmp_path / "personal-context-commit-unknown.sqlite3"
    ledger = DisconnectedContextReplayLedger(path, create=True)
    genesis = ledger.witness()
    first = _binding(1)
    second = _binding(2)
    native_open = ledger._open
    commit_attempts = 0

    class CommitBoundary:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def commit(self) -> None:
            nonlocal commit_attempts
            commit_attempts += 1
            if durable:
                self.connection.commit()
            else:
                self.connection.rollback()
            raise sqlite3.OperationalError(
                "synthetic context COMMIT acknowledgement lost"
            )

        def rollback(self) -> None:
            self.connection.rollback()

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name):
            return getattr(self.connection, name)

    # Inject only at this ledger instance's write boundary. The real SQLite
    # connection and on-disk transaction remain local and disposable.
    ledger._open = lambda *, read_only=False: CommitBoundary(
        native_open(read_only=read_only),
    )

    with pytest.raises(
        sqlite3.OperationalError,
        match="context COMMIT acknowledgement lost",
    ):
        ledger.reserve(first, retained=genesis)

    # The ambiguous COMMIT is attempted once. The caller receives no receipt;
    # the exception path never retries the reservation.
    assert commit_attempts == 1

    cold = DisconnectedContextReplayLedger(path)
    observed = cold.witness()
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT seq,request_id,owner_digest,context_digest,binding_digest,chain_sha256 "
            "FROM context_requests ORDER BY seq",
        ).fetchall()
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)

    if durable:
        assert observed.count == 1
        assert observed.chain_sha256 != genesis.chain_sha256
        assert len(rows) == 1
        assert rows[0][0] == 1
        assert rows[0][1] == first.request_id
        with pytest.raises(
            OfflineContextReplayRejected,
            match="stale retained",
        ):
            cold.reserve(second, retained=genesis)
        with pytest.raises(
            OfflineContextReplayRejected,
            match="duplicate",
        ):
            cold.reserve(first, retained=observed)
    else:
        assert observed.count == 0
        assert observed.chain_sha256 == genesis.chain_sha256
        assert rows == []

    assert commit_attempts == 1
    assert _CONTENT.encode("utf-8") not in path.read_bytes()
    assert cold.witness() == observed
