"""Run1018: a lost COMMIT acknowledgement cannot replay a context reservation.

Only synthetic identifiers, synthetic fixture text and disposable local SQLite
are used. A reservation is not consent, disclosure or Tool dispatch authority.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3

import pytest

import ark.personal_context_replay_ledger as replay
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_request_binding import bind_offline_context_request


_OWNER = "a" * 64
_SCOPE = "b" * 64
_RECORD = "rec_" + "c" * 32
_PAYLOAD = "synthetic-only-private-context"


def _binding(index: int):
    item = OfflineContextFixture(
        _RECORD,
        _OWNER,
        _SCOPE,
        _PAYLOAD,
        hashlib.sha256(_PAYLOAD.encode("utf-8")).hexdigest(),
        1000,
    )
    preview = build_offline_context_preview(
        (item,),
        owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,),
        observed_at_ms=100,
    )
    return bind_offline_context_request(
        "ctxreq_" + f"{index:064x}",
        preview,
    )


def test_lost_commit_acknowledgement_keeps_one_reservation_and_denies_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "context-commit-unknown.sqlite3"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    retained = ledger.witness()
    binding = _binding(1)

    native_connect = sqlite3.connect
    target = path.as_uri() + "?mode=rw"
    committed: list[bool] = []
    rolled_back: list[bool] = []

    class CommitAcknowledgementLost:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def execute(self, *args, **kwargs):
            return self.connection.execute(*args, **kwargs)

        def commit(self) -> None:
            # The native COMMIT succeeds; only its acknowledgement is lost.
            self.connection.commit()
            committed.append(True)
            raise sqlite3.OperationalError(
                "synthetic COMMIT acknowledgement lost",
            )

        def rollback(self) -> None:
            rolled_back.append(True)
            self.connection.rollback()

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    def connect(database, *args, **kwargs):
        connection = native_connect(database, *args, **kwargs)
        if database == target:
            return CommitAcknowledgementLost(connection)
        return connection

    with monkeypatch.context() as scoped:
        scoped.setattr(replay.sqlite3, "connect", connect)
        with pytest.raises(
            sqlite3.OperationalError,
            match="COMMIT acknowledgement lost",
        ):
            ledger.reserve(binding, retained=retained)

    assert committed == [True]
    assert rolled_back == [True]

    # Cold readback is the only evidence available after the caller lost its
    # receipt. It must not manufacture a new receipt or replay authority.
    reopened = replay.DisconnectedContextReplayLedger(path)
    current = reopened.witness()
    assert current.count == 1
    assert current.chain_sha256 != retained.chain_sha256
    assert current.independent_custody_proven is False

    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT seq,request_id,owner_digest,context_digest,"
            "binding_digest,chain_sha256 FROM context_requests ORDER BY seq"
        ).fetchall()
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert len(rows) == 1
    assert rows[0][0] == 1
    assert rows[0][1] == binding.request_id
    assert _PAYLOAD not in repr(rows)

    # The pre-COMMIT witness is stale; a different request cannot append.
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="stale retained context request history",
    ):
        reopened.reserve(_binding(2), retained=retained)

    # Even a fresh local witness cannot make the same request ID repeat.
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="duplicate context request identity",
    ):
        reopened.reserve(binding, retained=current)

    assert reopened.witness() == current
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM context_requests"
        ).fetchone() == (1,)
