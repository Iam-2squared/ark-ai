"""Restart a disconnected recovery review from a detached JSON witness.

All fixtures are synthetic. No ToolBackend method is called, even when a
Planner journal claims local success or a persisted reservation is present.
"""

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

import ark.agency.synthetic_recovery_archive_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_recovery_triage import review_synthetic_write_recovery


class _NoBackend:
    def execute(self, call):
        raise AssertionError("recovery archive must never execute the backend")


def _fixture(folder: Path):
    call = ToolCall("local", "mock.write", "offline", {"fixture": 1})
    steps = (PlanStep("root", call),)
    journal = SyntheticPlanJournal(folder / "plan.sqlite", steps)
    ledger_path = folder / "ledger.sqlite"
    store = SyntheticOccurrenceStore(ledger_path)
    audit = SQLiteActionAudit(folder / "audit.sqlite", clock_ms=lambda: 20)
    registry = ToolRegistry((
        ToolRegistration("local", "mock.write", Effect.WRITE, "never", _NoBackend()),
    ))
    return call, steps, journal, ledger_path, store, audit, registry


def _capture(state):
    call, _steps, journal, ledger, _store, audit, registry = state
    review = review_synthetic_write_recovery(
        journal, ledger, audit, registry, call, step_id="root",
    )
    return module.archive_synthetic_recovery(review)


def _reopened(state, anchor):
    call, steps, journal, ledger, _store, audit, registry = state
    del journal, audit
    return module.recheck_synthetic_recovery_archive(
        anchor, SyntheticPlanJournal(state[2]._path, steps),
        ledger, SQLiteActionAudit(state[5].path, clock_ms=lambda: 20),
        registry, call,
    )


def _retag(raw):
    return module.SyntheticRecoveryArchive(
        raw, "srecovery_" + hashlib.sha256(
            b"ARK-synthetic-recovery-archive-v1\0" + raw,
        ).hexdigest(),
    )


def test_empty_reopened_archive_is_deterministic_and_never_authorizes(tmp_path):
    state = _fixture(tmp_path)
    one = _capture(state)
    two = _capture(state)
    assert one == two
    assert b"fixture" not in one.canonical_json
    assert _reopened(state, one).step_state == "pending"
    assert not one.dispatch_authorized
    assert not one.automatic_replay_authorized
    assert not one.external_outcome_known


def test_reopened_running_remains_unknown_and_cannot_replay(tmp_path):
    state = _fixture(tmp_path)
    anchor = _capture(state)
    state[2].append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    fresh = _reopened(state, anchor)
    assert fresh.step_state == "running"
    assert fresh.ambiguous_write
    assert not fresh.external_outcome_known
    assert not fresh.automatic_replay_authorized


def test_retained_reservation_survives_reopen_but_not_as_external_receipt(tmp_path):
    state = _fixture(tmp_path)
    call, _steps, _journal, _ledger, store, _audit, registry = state
    store.reserve_synthetic(
        registry, call, OneShotAuthorization("first", call.request_id, 1000),
        occurrence_id="occ_" + "1" * 64, now_ms=11,
    )
    anchor = _capture(state)
    fresh = _reopened(state, anchor)
    assert fresh.matching_occurrences == ("occ_" + "1" * 64,)
    assert not fresh.external_outcome_known


def test_retained_reservation_rollback_is_refused_after_restart(tmp_path):
    state = _fixture(tmp_path)
    call, _steps, _journal, ledger, store, _audit, registry = state
    store.reserve_synthetic(
        registry, call, OneShotAuthorization("one", call.request_id, 1000),
        occurrence_id="occ_" + "2" * 64, now_ms=11,
    )
    anchor = _capture(state)
    with sqlite3.connect(ledger) as conn:
        conn.execute("DELETE FROM synthetic_occurrence_reservations")
    with pytest.raises(Exception, match="retained reservation history changed"):
        _reopened(state, anchor)


@pytest.mark.parametrize("change", ("bytes", "digest", "noncanonical", "version", "extra"))
def test_corrupt_or_noncanonical_detached_archives_are_rejected(tmp_path, change):
    state = _fixture(tmp_path)
    anchor = _capture(state)
    if change == "bytes":
        bad = module.SyntheticRecoveryArchive(anchor.canonical_json + b" ", anchor.digest)
    elif change == "digest":
        bad = module.SyntheticRecoveryArchive(anchor.canonical_json, "srecovery_" + "f" * 64)
    else:
        payload = json.loads(anchor.canonical_json)
        if change == "version":
            payload["version"] = 2
        if change == "extra":
            payload["unexpected"] = "forged"
        if change == "noncanonical":
            raw = json.dumps(payload, indent=2).encode("utf-8")
        else:
            raw = json.dumps(
                payload, ensure_ascii=True, sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        bad = _retag(raw)
    expected = {
        "bytes": "archive bytes or digest changed",
        "digest": "archive bytes or digest changed",
        "noncanonical": "noncanonical recovery archive",
        "version": "unsupported archive version",
        "extra": "archive shape changed",
    }
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match=expected[change]):
        _reopened(state, bad)


@pytest.mark.parametrize("malformed", ("plan", "ledger", "audit", "link"))
def test_structurally_valid_digest_cannot_certify_bad_retained_witness(
    tmp_path, malformed,
):
    state = _fixture(tmp_path)
    payload = json.loads(_capture(state).canonical_json)
    if malformed == "plan":
        payload["plan"]["event_count"] = "forged"
    elif malformed == "ledger":
        payload["ledger"]["row_hashes"] = ["invalid-hash"]
    elif malformed == "audit":
        payload["audit"]["chain_sha256"] = "invalid-hash"
    else:
        payload["link"] = {
            "event_count": 0, "tail_hash": "invalid-hash",
            "last_link_at_ms": -1,
        }
    raw = json.dumps(
        payload, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="invalid recovery archive"):
        _reopened(state, _retag(raw))


def test_reopen_rejects_action_with_different_request_identity(tmp_path):
    state = _fixture(tmp_path)
    anchor = _capture(state)
    other = ToolCall("local", "mock.write", "offline", {"fixture": 2})
    with pytest.raises(Exception, match="plan step action|reopened recovery differs"):
        module.recheck_synthetic_recovery_archive(
            anchor, state[2], state[3], state[5], state[6], other,
        )


def test_archive_changed_during_db_callback_fails_closed(tmp_path, monkeypatch):
    state = _fixture(tmp_path)
    anchor = _capture(state)
    original = module.review_synthetic_write_recovery

    def replace_after_review(*args, **kwargs):
        outcome = original(*args, **kwargs)
        object.__setattr__(anchor, "digest", "srecovery_" + "0" * 64)
        return outcome

    monkeypatch.setattr(module, "review_synthetic_write_recovery", replace_after_review)
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="archive changed"):
        _reopened(state, anchor)
