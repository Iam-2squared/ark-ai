"""Run1437: local V3 attempt receipts fail closed across restart and COMMIT ambiguity."""

from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

import ark.learning.attempt_ledger as ledger_module
from ark.learning.attempt_ledger import (
    AttemptLedgerCommitUnknown,
    AttemptLedgerConflictError,
    AttemptLedgerSchemaError,
    SQLiteAttemptLedger,
)


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _attempt(label: str) -> str:
    return "attempt_" + _sha(label)


def _case(tmp_path: Path):
    path = tmp_path / "attempts.sqlite"
    ledger = SQLiteAttemptLedger(path)
    execution = _sha("synthetic execution snapshot")
    authorization = _sha("synthetic authorization packet")
    return path, ledger, execution, authorization


def test_started_attempt_recovers_as_manual_review_only(tmp_path: Path):
    _, ledger, execution, authorization = _case(tmp_path)
    started = ledger.begin_attempt(
        _attempt("started"), execution, authorization, now_ms=100,
    )

    recovered = ledger.recover(started.attempt_id)
    assert recovered.receipt == started
    assert recovered.receipt.state == "STARTED"
    assert recovered.manual_review_required is True
    assert recovered.automatic_replay_authorized is False
    assert recovered.external_compute_authorized is False
    assert recovered.candidate_generation_authorized is False
    assert recovered.protected_v2_authorized is False
    assert recovered.promotion_authorized is False


def test_execution_snapshot_can_never_be_reserved_twice(tmp_path: Path):
    _, ledger, execution, authorization = _case(tmp_path)
    first = ledger.begin_attempt(
        _attempt("first"), execution, authorization, now_ms=100,
    )

    with pytest.raises(AttemptLedgerConflictError, match="already reserved"):
        ledger.begin_attempt(
            _attempt("second"), execution, authorization, now_ms=101,
        )
    with pytest.raises(AttemptLedgerConflictError, match="already reserved"):
        ledger.begin_attempt(
            first.attempt_id, _sha("different execution"), authorization, now_ms=102,
        )

    recovered = ledger.recover(first.attempt_id)
    assert recovered.receipt.state == "STARTED"
    assert recovered.manual_review_required is True


def test_finalization_is_one_way_and_carries_only_artifact_digests(tmp_path: Path):
    _, ledger, execution, authorization = _case(tmp_path)
    attempt_id = _attempt("finalized")
    ledger.begin_attempt(attempt_id, execution, authorization, now_ms=100)

    manifest = _sha("synthetic artifact manifest bytes")
    evidence = _sha("synthetic evidence bundle bytes")
    finalized = ledger.finalize_attempt(
        attempt_id,
        execution,
        authorization,
        artifact_manifest_sha256=manifest,
        evidence_bundle_sha256=evidence,
        now_ms=200,
    )
    assert finalized.state == "FINALIZED"
    assert finalized.event_sequence == 2
    assert finalized.artifact_manifest_sha256 == manifest
    assert finalized.evidence_bundle_sha256 == evidence
    assert finalized.automatic_replay_authorized is False
    assert finalized.candidate_generation_authorized is False
    assert finalized.promotion_authorized is False

    recovered = ledger.recover(attempt_id)
    assert recovered.receipt == finalized
    assert recovered.manual_review_required is False
    with pytest.raises(AttemptLedgerConflictError, match="already finalized"):
        ledger.finalize_attempt(
            attempt_id,
            execution,
            authorization,
            artifact_manifest_sha256=manifest,
            evidence_bundle_sha256=evidence,
            now_ms=201,
        )


class _CommitThenRaise:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        self._armed = True

    def execute(self, sql: str, *args, **kwargs):
        result = self._connection.execute(sql, *args, **kwargs)
        if sql == "COMMIT" and self._armed:
            self._armed = False
            raise sqlite3.OperationalError("synthetic lost COMMIT acknowledgement")
        return result

    def __getattr__(self, name: str):
        return getattr(self._connection, name)


def _lose_one_path_commit(monkeypatch, path: Path):
    native_connect = sqlite3.connect
    uri_prefix = path.resolve().as_uri()

    def injected_connect(database, *args, **kwargs):
        connection = native_connect(database, *args, **kwargs)
        if database != ":memory:" and str(database).startswith(uri_prefix):
            return _CommitThenRaise(connection)
        return connection

    monkeypatch.setattr(ledger_module.sqlite3, "connect", injected_connect)


def test_start_commit_unknown_is_resolved_by_cold_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    path, ledger, execution, authorization = _case(tmp_path)
    attempt_id = _attempt("start-commit-unknown")
    _lose_one_path_commit(monkeypatch, path)

    with pytest.raises(AttemptLedgerCommitUnknown, match="cold recovery required"):
        ledger.begin_attempt(attempt_id, execution, authorization, now_ms=100)

    monkeypatch.undo()
    recovered = SQLiteAttemptLedger(path).recover(attempt_id)
    assert recovered.receipt.state == "STARTED"
    assert recovered.manual_review_required is True
    with pytest.raises(AttemptLedgerConflictError, match="already reserved"):
        recovered_ledger = SQLiteAttemptLedger(path)
        recovered_ledger.begin_attempt(
            _attempt("retry"), execution, authorization, now_ms=101,
        )


def test_finalization_commit_unknown_is_resolved_without_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    path, ledger, execution, authorization = _case(tmp_path)
    attempt_id = _attempt("finalize-commit-unknown")
    ledger.begin_attempt(attempt_id, execution, authorization, now_ms=100)
    manifest = _sha("manifest")
    evidence = _sha("evidence")
    _lose_one_path_commit(monkeypatch, path)

    with pytest.raises(AttemptLedgerCommitUnknown, match="cold recovery required"):
        ledger.finalize_attempt(
            attempt_id,
            execution,
            authorization,
            artifact_manifest_sha256=manifest,
            evidence_bundle_sha256=evidence,
            now_ms=200,
        )

    monkeypatch.undo()
    recovered = SQLiteAttemptLedger(path).recover(attempt_id)
    assert recovered.receipt.state == "FINALIZED"
    assert recovered.receipt.artifact_manifest_sha256 == manifest
    assert recovered.receipt.evidence_bundle_sha256 == evidence
    assert recovered.manual_review_required is False
    with pytest.raises(AttemptLedgerConflictError, match="already finalized"):
        SQLiteAttemptLedger(path).finalize_attempt(
            attempt_id,
            execution,
            authorization,
            artifact_manifest_sha256=manifest,
            evidence_bundle_sha256=evidence,
            now_ms=201,
        )


def test_two_handles_cannot_reserve_the_same_execution_snapshot(tmp_path: Path):
    path = tmp_path / "attempt-race.sqlite"
    first = SQLiteAttemptLedger(path)
    second = SQLiteAttemptLedger(path)
    execution = _sha("racing synthetic execution")
    authorization = _sha("racing synthetic authorization")
    barrier = Barrier(2)

    def reserve(ledger: SQLiteAttemptLedger, label: str):
        barrier.wait()
        try:
            return ledger.begin_attempt(
                _attempt(label), execution, authorization, now_ms=100,
            )
        except AttemptLedgerConflictError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(
            lambda item: reserve(*item),
            ((first, "race-a"), (second, "race-b")),
        ))
    assert sum(result is not None for result in results) == 1
    winner = next(result for result in results if result is not None)
    assert SQLiteAttemptLedger(path).recover(winner.attempt_id).receipt == winner


def test_event_hash_corruption_is_rejected_before_recovery(tmp_path: Path):
    path, ledger, execution, authorization = _case(tmp_path)
    started = ledger.begin_attempt(
        _attempt("tamper"), execution, authorization, now_ms=100,
    )
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE attempt_events SET event_sha256=? WHERE sequence=1",
            ("0" * 64,),
        )

    with pytest.raises(AttemptLedgerSchemaError, match="event hash mismatch"):
        ledger.recover(started.attempt_id)
