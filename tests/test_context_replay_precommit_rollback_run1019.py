"""Run1019: a pre-COMMIT failure leaves no Personal Context reservation.

Synthetic identifiers and disposable local SQLite only. The ledger is not
consent, disclosure, or Tool dispatch authority.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

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


def _binding():
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
        "ctxreq_" + f"{1:064x}",
        preview,
    )


def test_precommit_failure_rolls_back_reservation_and_cold_readback_is_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "context-precommit-rollback.sqlite3"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    retained = ledger.witness()
    binding = _binding()

    native_connect = sqlite3.connect
    target = path.as_uri() + "?mode=rw"
    commit_attempts: list[bool] = []
    native_commits: list[bool] = []
    rollbacks: list[bool] = []

    class CommitFailsBeforeNative:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def commit(self) -> None:
            # Fail at the COMMIT boundary without invoking native COMMIT.
            commit_attempts.append(True)
            raise sqlite3.OperationalError(
                "synthetic COMMIT failure before native commit",
            )

        def execute(self, *args, **kwargs):
            return self.connection.execute(*args, **kwargs)

        def rollback(self) -> None:
            rollbacks.append(True)
            self.connection.rollback()

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    def connect(database, *args, **kwargs):
        connection = native_connect(database, *args, **kwargs)
        if database == target:
            return CommitFailsBeforeNative(connection)
        return connection

    with monkeypatch.context() as scoped:
        scoped.setattr(replay.sqlite3, "connect", connect)
        with pytest.raises(
            sqlite3.OperationalError,
            match="COMMIT failure before native commit",
        ):
            ledger.reserve(binding, retained=retained)

    assert commit_attempts == [True]
    assert native_commits == []
    assert rollbacks == [True]

    # Only a cold, read-only verification may establish that this synthetic
    # attempt left the local history unchanged. It does not prove independent
    # custody, trusted time, consent, disclosure, or external effects.
    reopened = replay.DisconnectedContextReplayLedger(path)
    current = reopened.verify_retained_prefix(retained)
    assert current == retained
    assert current.count == 0
    assert current.chain_sha256 == retained.chain_sha256

    with native_connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM context_requests",
        ).fetchone() == (0,)
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
