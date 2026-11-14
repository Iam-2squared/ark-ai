"""Older Context request chains must survive valid-looking later appends."""

import sqlite3
from dataclasses import replace

import pytest

import ark.personal_context_replay_ledger as replay
import ark.personal_context_replay_prefix_review as context_prefix
from ark.personal_context_request_binding import OfflineContextRequestBinding


def _binding(index):
    return OfflineContextRequestBinding(
        "ctxreq_" + f"{index:064x}", "a" * 64, "b" * 64, 1, "c" * 64,
    )


def _ledger(tmp_path):
    return replay.DisconnectedContextReplayLedger(
        tmp_path / "context.db", create=True,
    )


def _first(tmp_path):
    ledger = _ledger(tmp_path)
    receipt = ledger.reserve(
        _binding(1), retained=replay.genesis_offline_context_replay_witness(),
    )
    return ledger, receipt.witness


def _append(ledger, retained):
    return ledger.reserve(_binding(2), retained=retained).witness


def test_empty_genesis_is_content_free_and_does_not_grant_authority(tmp_path):
    ledger = _ledger(tmp_path)
    retained = replay.genesis_offline_context_replay_witness()
    report = context_prefix.review_retained_context_replay_prefix(ledger, retained)
    assert (report.retained_count, report.current_count) == (0, 0)
    assert report.status == "UNCHANGED_LOCAL_HISTORY"
    assert report.historical_writer_authenticated is False
    assert report.independent_custody_proven is False
    assert report.consent_verified is False
    assert report.revocation_freshness_verified is False
    assert report.context_disclosure_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.automatic_replay_authorized is False


def test_valid_appended_request_stays_unverified(tmp_path):
    ledger, old = _first(tmp_path)
    _append(ledger, old)
    result = context_prefix.review_retained_context_replay_prefix(ledger, old)
    assert (result.retained_count, result.current_count) == (1, 2)
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.current_chain_sha256 == ledger.witness().chain_sha256


def test_unmodified_chain_is_deterministic_across_restart(tmp_path):
    ledger, old = _first(tmp_path)
    reopened = replay.DisconnectedContextReplayLedger(ledger._path)
    one = context_prefix.review_retained_context_replay_prefix(reopened, old)
    two = context_prefix.review_retained_context_replay_prefix(reopened, old)
    assert one == two
    assert one.status == "UNCHANGED_LOCAL_HISTORY"
    assert "private" not in repr(one)


def test_recomputed_consistent_history_still_rejects_old_prefix(tmp_path):
    ledger, old = _first(tmp_path)
    _append(ledger, old)
    with sqlite3.connect(ledger._path) as conn:
        rows = conn.execute(
            "SELECT seq,request_id,owner_digest,context_digest,binding_digest "
            "FROM context_requests ORDER BY seq"
        ).fetchall()
        first, second = rows
        changed_owner = "f" * 64
        changed_first = replay._hash((
            "row", replay.genesis_offline_context_replay_witness().chain_sha256,
            first[0], first[1], changed_owner, first[3], first[4],
        ))
        changed_second = replay._hash((
            "row", changed_first, second[0], second[1],
            second[2], second[3], second[4],
        ))
        conn.execute(
            "UPDATE context_requests SET owner_digest=?,chain_sha256=? WHERE seq=1",
            (changed_owner, changed_first),
        )
        conn.execute(
            "UPDATE context_requests SET chain_sha256=? WHERE seq=2",
            (changed_second,),
        )
    # This is a locally consistent NEW SHA chain; only the caller-retained
    # prefix captures the historical substitution.
    assert ledger.witness().count == 2
    with pytest.raises(context_prefix.OfflineContextPrefixRejected, match="prefix"):
        context_prefix.review_retained_context_replay_prefix(ledger, old)


def test_same_count_rewrite_denied(tmp_path):
    ledger, old = _first(tmp_path)
    with sqlite3.connect(ledger._path) as conn:
        conn.execute(
            "UPDATE context_requests SET owner_digest=?",
            ("f" * 64,),
        )
    with pytest.raises(context_prefix.OfflineContextPrefixRejected):
        context_prefix.review_retained_context_replay_prefix(ledger, old)


def test_retained_count_rollback_denied(tmp_path):
    ledger, old = _first(tmp_path)
    later = _append(ledger, old)
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("DELETE FROM context_requests WHERE seq=2")
    with pytest.raises(context_prefix.OfflineContextPrefixRejected, match="rolled back"):
        context_prefix.review_retained_context_replay_prefix(ledger, later)


@pytest.mark.parametrize(
    "changes", [
        {"count": True},
        {"count": 2},
        {"chain_sha256": "x" * 64},
        {"chain_sha256": "0" * 64},
    ],
)
def test_forged_or_mismatched_prior_witness_denied(tmp_path, changes):
    ledger, old = _first(tmp_path)
    forged = replace(old, **changes)
    with pytest.raises(context_prefix.OfflineContextPrefixRejected):
        context_prefix.review_retained_context_replay_prefix(ledger, forged)


def test_readonly_review_does_not_modify_context_ledger(tmp_path):
    ledger, old = _first(tmp_path)
    _append(ledger, old)
    with sqlite3.connect(ledger._path) as conn:
        before = tuple(conn.iterdump())
    context_prefix.review_retained_context_replay_prefix(ledger, old)
    with sqlite3.connect(ledger._path) as conn:
        assert tuple(conn.iterdump()) == before


def test_source_retarget_during_scan_is_denied(tmp_path, monkeypatch):
    ledger, old = _first(tmp_path)
    original = replay._inspect

    def retarget(conn):
        result = original(conn)
        ledger._path = tmp_path / "other.db"
        return result

    monkeypatch.setattr(replay, "_inspect", retarget)
    with pytest.raises(context_prefix.OfflineContextPrefixRejected, match="source"):
        context_prefix.review_retained_context_replay_prefix(ledger, old)


def test_witness_reflective_mutation_during_scan_is_denied(tmp_path, monkeypatch):
    ledger, old = _first(tmp_path)
    original = replay._inspect

    def retarget(conn):
        result = original(conn)
        object.__setattr__(old, "chain_sha256", "0" * 64)
        return result

    monkeypatch.setattr(replay, "_inspect", retarget)
    with pytest.raises(context_prefix.OfflineContextPrefixRejected, match="witness"):
        context_prefix.review_retained_context_replay_prefix(ledger, old)


def test_denial_only_result_cannot_claim_consent(tmp_path, monkeypatch):
    ledger, old = _first(tmp_path)
    monkeypatch.setattr(
        context_prefix.OfflineContextPrefixReview,
        "consent_verified",
        property(lambda self: True),
    )
    with pytest.raises(context_prefix.OfflineContextPrefixRejected, match="authority"):
        context_prefix.review_retained_context_replay_prefix(ledger, old)


def test_requires_exact_ledger_and_witness_types(tmp_path):
    ledger, old = _first(tmp_path)
    with pytest.raises(context_prefix.OfflineContextPrefixRejected):
        context_prefix.review_retained_context_replay_prefix(object(), old)
    with pytest.raises(context_prefix.OfflineContextPrefixRejected):
        context_prefix.review_retained_context_replay_prefix(ledger, object())
