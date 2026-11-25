"""Run1442: Personal Context replay CAS across independent processes.

Only synthetic fixture identities and local SQLite are used. The ledger never
stores fixture plaintext and its receipts do not authorize disclosure or tools.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from multiprocessing import get_context
from pathlib import Path

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
_PRIVATE = "synthetic private payload never stored in replay ledger"


def _binding(index: int):
    fixture = OfflineContextFixture(
        _RECORD,
        _OWNER,
        _SCOPE,
        _PRIVATE,
        hashlib.sha256(_PRIVATE.encode("utf-8")).hexdigest(),
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


def _reserve_worker(path: str, index: int, ready, release, results) -> None:
    ledger = DisconnectedContextReplayLedger(Path(path))
    binding = _binding(index)
    retained = genesis_offline_context_replay_witness()
    ready.put("ready")
    if not release.wait(timeout=45):
        raise RuntimeError("context replay race release timed out")
    try:
        receipt = ledger.reserve(binding, retained=retained)
    except OfflineContextReplayRejected as exc:
        results.put(("conflict", str(exc)))
    else:
        results.put((
            "success",
            receipt.request_id,
            receipt.witness.count,
            receipt.consent_verified,
            receipt.revocation_freshness_verified,
            receipt.context_disclosure_authorized,
            receipt.tool_dispatch_authorized,
            receipt.automatic_replay_authorized,
        ))


def _race(path: Path, indexes: tuple[int, int]) -> list[tuple[object, ...]]:
    context = get_context("spawn")
    ready = context.Queue()
    results = context.Queue()
    release = context.Event()
    processes = [
        context.Process(
            target=_reserve_worker,
            args=(os.fspath(path), index, ready, release, results),
        )
        for index in indexes
    ]
    try:
        for process in processes:
            process.start()
        assert [ready.get(timeout=60) for _ in processes] == ["ready", "ready"]
        release.set()
        outcomes = [results.get(timeout=60) for _ in processes]
        for process in processes:
            process.join(timeout=60)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        assert [process.exitcode for process in processes] == [0, 0]
        assert sorted(outcome[0] for outcome in outcomes) == ["conflict", "success"]
        return outcomes
    finally:
        release.set()
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        ready.close()
        results.close()


def _assert_denial_only_success(outcome: tuple[object, ...]) -> str:
    assert outcome[0] == "success"
    assert outcome[2] == 1
    assert outcome[3:] == (False, False, False, False, False)
    return outcome[1]


def test_same_context_request_reserved_once_across_two_processes_run1442(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context-replay-same-request-race.sqlite3"
    DisconnectedContextReplayLedger(path, create=True)
    outcomes = _race(path, (1, 1))
    winner = next(outcome for outcome in outcomes if outcome[0] == "success")
    request_id = _assert_denial_only_success(winner)

    cold = DisconnectedContextReplayLedger(path)
    tip = cold.witness()
    assert tip.count == 1
    assert request_id == _binding(1).request_id
    assert cold.verify_retained_prefix(genesis_offline_context_replay_witness()) == tip
    with pytest.raises(OfflineContextReplayRejected, match="duplicate"):
        cold.reserve(_binding(1), retained=tip)
    assert cold.witness() == tip
    assert _PRIVATE.encode("utf-8") not in path.read_bytes()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute("SELECT COUNT(*) FROM context_requests").fetchone() == (1,)


def test_disjoint_requests_need_cold_readback_after_cross_process_cas_loss_run1442(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context-replay-disjoint-request-race.sqlite3"
    DisconnectedContextReplayLedger(path, create=True)
    outcomes = _race(path, (1, 2))
    winner = next(outcome for outcome in outcomes if outcome[0] == "success")
    winner_id = _assert_denial_only_success(winner)

    cold = DisconnectedContextReplayLedger(path)
    first_tip = cold.witness()
    assert first_tip.count == 1
    winner_index = 1 if winner_id == _binding(1).request_id else 2
    loser_index = 2 if winner_index == 1 else 1
    loser = _binding(loser_index)

    # A stale genesis witness never auto-refreshes or retries. Only an
    # explicit cold readback supplies the current prefix for a later attempt.
    receipt = cold.reserve(loser, retained=first_tip)
    assert receipt.request_id == loser.request_id
    assert receipt.witness.count == 2
    assert receipt.context_disclosure_authorized is False
    assert receipt.tool_dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert cold.verify_retained_prefix(first_tip) == receipt.witness
    assert cold.verify_retained_prefix(
        genesis_offline_context_replay_witness()
    ) == receipt.witness
    assert _PRIVATE.encode("utf-8") not in path.read_bytes()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute("SELECT COUNT(*) FROM context_requests").fetchone() == (2,)
