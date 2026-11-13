"""Bound synthetic Personal Context replay inspection before hash hydration.

Only exact, hash-only IDs in disposable SQLite fixtures. Neither a valid
receipt nor a retained prefix authorizes consent, export, or dispatch.
"""

from __future__ import annotations

import hashlib
import sqlite3

import pytest

from ark import personal_context_replay_ledger as replay
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_request_binding import bind_offline_context_request


def _binding():
    payload = "inert synthetic context"
    item = OfflineContextFixture(
        "rec_" + "c" * 32, "a" * 64, "b" * 64,
        payload, hashlib.sha256(payload.encode()).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (item,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + "1" * 64, preview)


def _stored(tmp_path):
    path = tmp_path / "inert-private-replay.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    receipt = ledger.reserve(
        _binding(), retained=replay.genesis_offline_context_replay_witness(),
    )
    return ledger, receipt.witness


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("request_id", sqlite3.Binary(b"ctxreq_fake")),
        ("request_id", "ctxreq_" + "f" * 65),
        ("owner_digest", sqlite3.Binary(b"owner")),
        ("context_digest", "e" * 65),
        ("binding_digest", "f" * 4096),
        ("chain_sha256", sqlite3.Binary(b"chain")),
    ),
)
def test_malformed_local_replay_row_denied_before_digest_callback(
    tmp_path, monkeypatch, column, replacement,
):
    ledger, _ = _stored(tmp_path)
    with sqlite3.connect(ledger._path) as conn:
        conn.execute(
            f"UPDATE context_requests SET {column}=? WHERE seq=1",
            (replacement,),
        )
    calls = []

    def forbidden_hash(*_args, **_kwargs):
        calls.append("private metadata")
        pytest.fail("malformed context request reached Python hashing")

    monkeypatch.setattr(replay, "_hash", forbidden_hash)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="width or storage type changed",
    ):
        ledger.witness()
    assert calls == []


def test_sqlite_count_over_budget_denied_before_hydration(
    tmp_path, monkeypatch,
):
    ledger, _ = _stored(tmp_path)
    monkeypatch.setattr(replay, "_MAX_ROWS", 0)

    def forbidden_hash(*_args, **_kwargs):
        pytest.fail("over-budget context requests reached Python hashing")

    monkeypatch.setattr(replay, "_hash", forbidden_hash)
    with pytest.raises(
        replay.OfflineContextReplayRejected, match="persisted row budget",
    ):
        ledger.witness()


def test_healthy_request_prefix_remains_read_only_and_deny_only(tmp_path):
    ledger, tip = _stored(tmp_path)
    with sqlite3.connect(ledger._path) as conn:
        before = tuple(conn.iterdump())
    reopened = replay.DisconnectedContextReplayLedger(ledger._path)
    reviewed = reopened.verify_retained_prefix(
        replay.genesis_offline_context_replay_witness(),
    )
    assert reviewed.count == tip.count == 1
    assert reviewed.chain_sha256 == tip.chain_sha256
    assert reviewed.independent_custody_proven is False
    with sqlite3.connect(ledger._path) as conn:
        assert tuple(conn.iterdump()) == before
