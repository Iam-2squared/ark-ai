"""Restart-local Personal Context replay prefix checks.

All inputs and reservations are disconnected fixtures. Prefix continuity is
not consent, cross-process custody, permission to disclose, or replay authority.
"""

import hashlib
import sqlite3
from dataclasses import replace

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


def _binding(digit: str):
    content = "synthetic context, not for disclosure"
    item = OfflineContextFixture(
        "rec_" + "c" * 32, "a" * 64, "b" * 64,
        content, hashlib.sha256(content.encode()).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (item,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + digit * 64, preview)


def _two(tmp_path):
    path = tmp_path / "context.sqlite"
    ledger = DisconnectedContextReplayLedger(path, create=True)
    first = ledger.reserve(
        _binding("1"), retained=genesis_offline_context_replay_witness(),
    ).witness
    second = ledger.reserve(_binding("2"), retained=first).witness
    return path, ledger, first, second


def test_empty_genesis_prefix_remains_valid_after_new_reservations(tmp_path):
    path, _, _, second = _two(tmp_path)
    reopened = DisconnectedContextReplayLedger(path)
    current = reopened.verify_retained_prefix(
        genesis_offline_context_replay_witness()
    )
    assert current.count == second.count == 2
    assert current.chain_sha256 == second.chain_sha256
    assert current.independent_custody_proven is False


def test_retained_first_reservation_matches_same_snapshot_after_restart(tmp_path):
    path, _, first, second = _two(tmp_path)
    reopened = DisconnectedContextReplayLedger(path)
    assert reopened.verify_retained_prefix(first) == second
    assert reopened.witness() == second


def test_forged_retained_prefix_is_rejected_without_new_rows(tmp_path):
    path, reopened, first, second = _two(tmp_path)
    forged = replace(first, chain_sha256="f" * 64)
    with pytest.raises(OfflineContextReplayRejected, match="prefix diverged"):
        reopened.verify_retained_prefix(forged)
    assert DisconnectedContextReplayLedger(path).witness() == second


def test_truncated_history_cannot_satisfy_later_retained_prefix(tmp_path):
    path, ledger, first, second = _two(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM context_requests WHERE seq=2")
    with pytest.raises(OfflineContextReplayRejected, match="beyond durable"):
        ledger.verify_retained_prefix(second)
    assert ledger.verify_retained_prefix(first) == first


def test_durable_chain_rebase_rejected_against_independent_prefix(tmp_path):
    path, ledger, first, _ = _two(tmp_path)
    from ark.personal_context_replay_ledger import (
        _hash,
        genesis_offline_context_replay_witness,
    )
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT seq,request_id,owner_digest,context_digest,binding_digest "
            "FROM context_requests ORDER BY seq"
        ).fetchall()
        assert len(rows) == 2
        previous = genesis_offline_context_replay_witness().chain_sha256
        for seq, request, owner, context, binding in rows:
            context = "f" * 64
            chain = _hash(("row", previous, seq, request, owner, context, binding))
            conn.execute(
                "UPDATE context_requests SET context_digest=?,chain_sha256=? WHERE seq=?",
                (context, chain, seq),
            )
            previous = chain
    with pytest.raises(OfflineContextReplayRejected, match="prefix diverged"):
        ledger.verify_retained_prefix(first)
    assert ledger.witness().count == 2


def test_review_never_materializes_missing_replay_database(tmp_path):
    path = tmp_path / "missing.sqlite"
    with pytest.raises(OfflineContextReplayRejected, match="missing"):
        DisconnectedContextReplayLedger(path)
    assert not path.exists()
