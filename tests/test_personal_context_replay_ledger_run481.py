"""Local Personal Context replay reservations: no live permissions or content."""

from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

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


def _binding(index=1, *, content="synthetic private payload"):
    fixture = OfflineContextFixture(
        _RECORD, _OWNER, _SCOPE, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (fixture,), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
    )
    return bind_offline_context_request(
        "ctxreq_" + f"{index:064x}", preview,
    )


def _ledger(tmp_path):
    return replay.DisconnectedContextReplayLedger(
        tmp_path / "context.db", create=True,
    )


def test_genesis_append_restart_and_no_authority(tmp_path):
    db = _ledger(tmp_path)
    genesis = replay.genesis_offline_context_replay_witness()
    assert db.witness() == genesis
    receipt = db.reserve(_binding(), retained=genesis)
    assert receipt.witness.count == 1
    assert receipt.request_id == _binding().request_id
    assert not receipt.consent_verified
    assert not receipt.revocation_freshness_verified
    assert not receipt.context_disclosure_authorized
    assert not receipt.tool_dispatch_authorized
    assert not receipt.automatic_replay_authorized
    assert not receipt.witness.independent_custody_proven
    reopened = replay.DisconnectedContextReplayLedger(tmp_path / "context.db")
    assert reopened.witness() == receipt.witness
    assert "synthetic private payload" not in repr(receipt)
    with sqlite3.connect(tmp_path / "context.db") as conn:
        assert "synthetic private payload" not in repr(
            conn.execute("SELECT * FROM context_requests").fetchall()
        )


def test_second_request_can_append_with_current_witness(tmp_path):
    db = _ledger(tmp_path)
    first = db.reserve(
        _binding(1), retained=replay.genesis_offline_context_replay_witness(),
    )
    second = db.reserve(_binding(2), retained=first.witness)
    assert second.witness.count == 2
    assert second.witness.chain_sha256 != first.witness.chain_sha256


def test_same_request_never_replays_even_with_new_binding(tmp_path):
    db = _ledger(tmp_path)
    first = db.reserve(
        _binding(), retained=replay.genesis_offline_context_replay_witness(),
    )
    with pytest.raises(replay.OfflineContextReplayRejected, match="duplicate"):
        db.reserve(_binding(content="changed synthetic"), retained=first.witness)
    assert db.witness() == first.witness


def test_stale_witness_after_commit_fail_closed(tmp_path):
    db = _ledger(tmp_path)
    old = replay.genesis_offline_context_replay_witness()
    db.reserve(_binding(), retained=old)
    with pytest.raises(replay.OfflineContextReplayRejected, match="stale"):
        db.reserve(_binding(2), retained=old)


def test_concurrent_same_witness_commits_at_most_once(tmp_path):
    db = _ledger(tmp_path)
    old = replay.genesis_offline_context_replay_witness()
    payload = _binding()

    def attempt(_):
        try:
            db.reserve(payload, retained=old)
        except replay.OfflineContextReplayRejected:
            return False
        return True

    with ThreadPoolExecutor(max_workers=6) as pool:
        outcomes = list(pool.map(attempt, range(12)))
    assert sum(outcomes) == 1
    assert db.witness().count == 1


@pytest.mark.parametrize("forged", [
    replace(_binding(), request_id="ctxreq_" + "f" * 63),
    replace(_binding(), request_id=True),
    replace(_binding(), owner_digest="F" * 64),
    replace(_binding(), record_count=True),
    object(),
])
def test_reject_forged_binding(forged, tmp_path):
    db = _ledger(tmp_path)
    with pytest.raises(replay.OfflineContextReplayRejected):
        db.reserve(
            forged, retained=replay.genesis_offline_context_replay_witness(),
        )
    assert db.witness().count == 0


@pytest.mark.parametrize("count", [True, 1.0, -1, 513])
def test_retained_witness_exact_type_and_count(count, tmp_path):
    db = _ledger(tmp_path)
    forged = replace(
        replay.genesis_offline_context_replay_witness(), count=count,
    )
    with pytest.raises(replay.OfflineContextReplayRejected, match="witness"):
        db.reserve(_binding(), retained=forged)


def test_missing_database_cannot_be_recreated_on_reopen(tmp_path):
    db = _ledger(tmp_path)
    db._path.unlink()
    with pytest.raises(replay.OfflineContextReplayRejected, match="missing"):
        db.witness()
    with pytest.raises(replay.OfflineContextReplayRejected, match="missing"):
        replay.DisconnectedContextReplayLedger(tmp_path / "context.db")
    assert not db._path.exists()


def test_schema_addition_denied_on_reopen(tmp_path):
    db = _ledger(tmp_path)
    with sqlite3.connect(db._path) as conn:
        conn.execute("CREATE TABLE injected(data TEXT)")
    with pytest.raises(replay.OfflineContextReplayRejected, match="schema"):
        replay.DisconnectedContextReplayLedger(db._path)


def test_persisted_digest_tamper_rejected(tmp_path):
    db = _ledger(tmp_path)
    db.reserve(
        _binding(), retained=replay.genesis_offline_context_replay_witness(),
    )
    with sqlite3.connect(db._path) as conn:
        conn.execute(
            "UPDATE context_requests SET context_digest=? WHERE seq=1",
            ("f" * 64,),
        )
    with pytest.raises(replay.OfflineContextReplayRejected, match="history changed"):
        db.witness()


def test_symlink_ancestor_and_hardlink_path_rejected(tmp_path):
    root = tmp_path / "actual"
    root.mkdir()
    db = replay.DisconnectedContextReplayLedger(
        root / "context.db", create=True,
    )
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(root, target_is_directory=True)
    except OSError:
        pytest.skip("symlink unavailable")
    with pytest.raises(replay.OfflineContextReplayRejected, match="ancestor"):
        replay.DisconnectedContextReplayLedger(alias / "context.db")
    linked = root / "linked.db"
    try:
        linked.hardlink_to(db._path)
    except OSError:
        pytest.skip("hardlink unavailable")
    with pytest.raises(replay.OfflineContextReplayRejected, match="aliased"):
        db.witness()


def test_postcommit_receipt_forgery_never_rolls_back(tmp_path, monkeypatch):
    db = _ledger(tmp_path)
    old = replay.genesis_offline_context_replay_witness()
    monkeypatch.setattr(
        replay, "OfflineContextReplayReceipt", lambda *args: object(),
    )
    with pytest.raises(replay.OfflineContextReplayRejected, match="postcommit"):
        db.reserve(_binding(), retained=old)
    assert db.witness().count == 1
    with pytest.raises(replay.OfflineContextReplayRejected, match="stale"):
        db.reserve(_binding(2), retained=old)


def test_binding_mutation_before_commit_is_rolled_back(tmp_path, monkeypatch):
    db = _ledger(tmp_path)
    item = _binding()
    original = replay._inspect
    changed = False

    def mutate(conn):
        nonlocal changed
        result = original(conn)
        if not changed:
            object.__setattr__(item, "context_digest", "f" * 64)
            changed = True
        return result

    monkeypatch.setattr(replay, "_inspect", mutate)
    with pytest.raises(replay.OfflineContextReplayRejected, match="changed"):
        db.reserve(
            item, retained=replay.genesis_offline_context_replay_witness(),
        )
    assert db.witness().count == 0


def test_configured_capacity_prevents_another_reservation(tmp_path, monkeypatch):
    db = _ledger(tmp_path)
    first = db.reserve(
        _binding(), retained=replay.genesis_offline_context_replay_witness(),
    )
    monkeypatch.setattr(replay, "_MAX_ROWS", 1)
    with pytest.raises(replay.OfflineContextReplayRejected, match="full"):
        db.reserve(_binding(2), retained=first.witness)
