"""Local Context replay reservations retain CAS safety across competing writers.

The SQLite store contains only synthetic hash identities; it cannot establish
human consent, independent custody, real data erasure, or external exactly-once.
"""

from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

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

PRIVATE = "synthetic-secret-never-stored-in-context-ledger"


def _binding(char):
    item = OfflineContextFixture(
        "rec_" + "c" * 32, "a" * 64, "b" * 64, PRIVATE,
        hashlib.sha256(PRIVATE.encode()).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (item,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + char * 64, preview)


def _compete(path, requests):
    DisconnectedContextReplayLedger(path, create=True)
    retained = genesis_offline_context_replay_witness()
    barrier = Barrier(2)

    def attempt(request):
        ledger = DisconnectedContextReplayLedger(path)
        barrier.wait(timeout=15)
        try:
            return ledger.reserve(request, retained=retained)
        except OfflineContextReplayRejected as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt, request) for request in requests]
        return retained, [future.result(timeout=30) for future in futures]


def test_same_identity_competing_writers_reserve_only_once(tmp_path):
    path = tmp_path / "shared-context.sqlite"
    retained, outcomes = _compete(path, (_binding("1"), _binding("1")))
    successes = [value for value in outcomes if not isinstance(
        value, OfflineContextReplayRejected,
    )]
    assert len(successes) == 1
    assert len(outcomes) - len(successes) == 1
    ledger = DisconnectedContextReplayLedger(path)
    tip = ledger.witness()
    assert tip.count == 1
    assert ledger.verify_retained_prefix(retained) == tip
    assert PRIVATE.encode() not in path.read_bytes()
    assert successes[0].context_disclosure_authorized is False
    assert successes[0].automatic_replay_authorized is False


def test_disjoint_competing_requests_require_fresh_cas_witness(tmp_path):
    path = tmp_path / "disjoint-context.sqlite"
    left, right = _binding("1"), _binding("2")
    retained, outcomes = _compete(path, (left, right))
    succeeded = [i for i, value in enumerate(outcomes) if not isinstance(
        value, OfflineContextReplayRejected,
    )]
    assert len(succeeded) == 1
    ledger = DisconnectedContextReplayLedger(path)
    first_tip = ledger.witness()
    assert first_tip.count == 1
    loser = (left, right)[1 - succeeded[0]]
    final = ledger.reserve(loser, retained=first_tip)
    assert final.witness.count == 2
    assert ledger.verify_retained_prefix(first_tip) == final.witness
    assert ledger.verify_retained_prefix(retained) == final.witness
    assert PRIVATE.encode() not in path.read_bytes()


def test_retained_prefix_rejects_history_rewrite_after_restart(tmp_path):
    path = tmp_path / "rewrite-context.sqlite"
    ledger = DisconnectedContextReplayLedger(path, create=True)
    first = ledger.reserve(
        _binding("1"), retained=genesis_offline_context_replay_witness(),
    )
    ledger.reserve(_binding("2"), retained=first.witness)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE context_requests SET owner_digest=? WHERE seq=1",
            ("f" * 64,),
        )
    restarted = DisconnectedContextReplayLedger
    with pytest.raises(OfflineContextReplayRejected):
        restarted(path)
    with pytest.raises(OfflineContextReplayRejected):
        ledger.verify_retained_prefix(first.witness)


def test_duplicate_request_stays_denied_after_restart_with_fresh_tip(tmp_path):
    path = tmp_path / "duplicate-context.sqlite"
    ledger = DisconnectedContextReplayLedger(path, create=True)
    first = ledger.reserve(
        _binding("1"), retained=genesis_offline_context_replay_witness(),
    )
    restarted = DisconnectedContextReplayLedger(path)
    with pytest.raises(OfflineContextReplayRejected, match="duplicate"):
        restarted.reserve(_binding("1"), retained=first.witness)
    assert restarted.witness() == first.witness
