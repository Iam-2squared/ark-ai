"""Cancellation fixture preserves local veto history but never verifies consent."""

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from ark.agency.synthetic_approval_cancellation_review import (
    SyntheticCancellationLedger,
    SyntheticCancellationRejected,
    SyntheticCancellationWitness,
)


def _approval(value: str) -> str:
    return "approval_" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _store(tmp_path: Path):
    path = tmp_path / "claims #1 ?.sqlite"
    return SyntheticCancellationLedger(path), path


def test_empty_local_status_never_implies_authorization(tmp_path: Path):
    ledger, _path = _store(tmp_path)
    state = ledger.review_state(_approval("first"))
    assert state.cancelled is False
    assert state.witness.event_count == 0
    assert state.witness.last_cancelled_at_ms == -1
    assert state.human_consent_verified is False
    assert state.dispatch_authorized is False
    assert state.automatic_replay_authorized is False


def test_cancel_survives_reopen_and_is_immutable_within_fixture(tmp_path: Path):
    ledger, path = _store(tmp_path)
    claim = _approval("first")
    witness = ledger.cancel_synthetic(claim, at_ms=10)
    assert witness.event_count == 1
    reopened = SyntheticCancellationLedger(path)
    state = reopened.review_state(claim, retained=witness)
    assert state.cancelled is True
    assert state.witness == witness
    with pytest.raises(SyntheticCancellationRejected, match="already persisted"):
        reopened.cancel_synthetic(claim, at_ms=11)
    assert reopened.read_witness() == witness


def test_other_claim_is_not_cancelled_by_an_unrelated_marker(tmp_path: Path):
    ledger, _path = _store(tmp_path)
    ledger.cancel_synthetic(_approval("one"), at_ms=10)
    assert ledger.review_state(_approval("two")).cancelled is False
    assert ledger.review_state(_approval("one")).cancelled is True


def test_append_allows_retained_prefix_and_newer_at(tmp_path: Path):
    ledger, _path = _store(tmp_path)
    earlier = ledger.cancel_synthetic(_approval("one"), at_ms=10)
    later = ledger.cancel_synthetic(_approval("two"), at_ms=10, retained=earlier)
    assert later.event_count == 2
    assert ledger.read_witness(retained=earlier) == later
    assert ledger.review_state(_approval("one"), retained=earlier).cancelled is True


def test_missing_earlier_row_detected_by_separately_retained_history(tmp_path: Path):
    ledger, path = _store(tmp_path)
    first = ledger.cancel_synthetic(_approval("one"), at_ms=10)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_claim_cancellations")
    assert ledger.read_witness().event_count == 0
    with pytest.raises(SyntheticCancellationRejected, match="retained"):
        ledger.read_witness(retained=first)
    with pytest.raises(SyntheticCancellationRejected, match="retained"):
        ledger.cancel_synthetic(_approval("two"), at_ms=12, retained=first)


def test_row_hash_tamper_is_rejected_before_read_or_write(tmp_path: Path):
    ledger, path = _store(tmp_path)
    ledger.cancel_synthetic(_approval("one"), at_ms=10)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE synthetic_claim_cancellations SET cancelled_at_ms=11"
        )
    with pytest.raises(SyntheticCancellationRejected, match="history changed"):
        ledger.read_witness()
    with pytest.raises(SyntheticCancellationRejected, match="history changed"):
        ledger.cancel_synthetic(_approval("two"), at_ms=12)


def test_schema_modification_rejected_without_auto_repair(tmp_path: Path):
    ledger, path = _store(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(SyntheticCancellationRejected, match="schema version"):
        ledger.review_state(_approval("one"))
    with pytest.raises(SyntheticCancellationRejected, match="schema version"):
        SyntheticCancellationLedger(path)


def test_missing_database_is_not_recreated_by_stale_object(tmp_path: Path):
    ledger, path = _store(tmp_path)
    path.rename(tmp_path / "moved.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        ledger.read_witness()
    with pytest.raises(sqlite3.OperationalError):
        ledger.cancel_synthetic(_approval("one"), at_ms=10)
    assert not path.exists()


@pytest.mark.parametrize("bad", ["", "approval_bad", "approval_" + "f" * 63, 17, True])
def test_approval_id_must_be_exact_canonical_digest(tmp_path: Path, bad):
    ledger, _path = _store(tmp_path)
    with pytest.raises(SyntheticCancellationRejected, match="invalid synthetic"):
        ledger.cancel_synthetic(bad, at_ms=10)
    with pytest.raises(SyntheticCancellationRejected, match="invalid synthetic"):
        ledger.review_state(bad)


@pytest.mark.parametrize("when", [-1, True, "10", 2**63])
def test_cancellation_timestamp_is_exact_sqlite_integer(tmp_path: Path, when):
    ledger, _path = _store(tmp_path)
    with pytest.raises(SyntheticCancellationRejected, match="invalid synthetic"):
        ledger.cancel_synthetic(_approval("one"), at_ms=when)


def test_regressing_cancellation_clock_rejected(tmp_path: Path):
    ledger, _path = _store(tmp_path)
    ledger.cancel_synthetic(_approval("first"), at_ms=12)
    with pytest.raises(SyntheticCancellationRejected, match="clock regression"):
        ledger.cancel_synthetic(_approval("second"), at_ms=11)
    assert ledger.read_witness().event_count == 1


@pytest.mark.parametrize("wrong", [False, 123, object()])
def test_retained_witness_requires_exact_dataclass(tmp_path: Path, wrong):
    ledger, _path = _store(tmp_path)
    with pytest.raises(SyntheticCancellationRejected, match="wrong type"):
        ledger.read_witness(retained=wrong)


def test_reflected_witness_change_is_rejected(tmp_path: Path):
    ledger, _path = _store(tmp_path)
    prior = ledger.cancel_synthetic(_approval("one"), at_ms=10)
    object.__setattr__(prior, "tail_hash", "cancel_" + "f" * 64)
    with pytest.raises(SyntheticCancellationRejected, match="retained"):
        ledger.read_witness(retained=prior)


def test_fake_empty_witness_is_rejected(tmp_path: Path):
    ledger, _path = _store(tmp_path)
    wrong = SyntheticCancellationWitness(0, "cancel_" + "f" * 64, -1)
    with pytest.raises(SyntheticCancellationRejected, match="invalid"):
        ledger.read_witness(retained=wrong)


def test_concurrent_local_cancellation_commits_once(tmp_path: Path):
    ledger, _path = _store(tmp_path)
    claim = _approval("once")

    def attempt(_ordinal):
        try:
            ledger.cancel_synthetic(claim, at_ms=10)
            return True
        except SyntheticCancellationRejected:
            return False

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(attempt, range(4)))
    assert results.count(True) == 1
    assert results.count(False) == 3
    assert ledger.read_witness().event_count == 1
