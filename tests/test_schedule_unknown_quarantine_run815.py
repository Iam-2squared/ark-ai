"""Disconnected scheduled quarantine COMMIT-UNKNOWN local triage tests."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

import ark.offline_schedule_unknown_quarantine_review as triage
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    QuarantineWitness,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)

_POLICY = QuarantinePolicy("a" * 64, 1000, 10000, 3, 1000)


def _setup(tmp_path: Path):
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(path, policy=_POLICY, create=True)
    return path, ledger, genesis_quarantine_witness(_POLICY)


def _review(ledger, retained, *, index=0, observed_ms=3000, policy=_POLICY):
    return triage.review_schedule_unknown_quarantine(
        ledger, policy, retained, index=index,
        occurrence_id=derive_quarantined_occurrence(policy, index),
        observed_ms=observed_ms,
    )


def _add(ledger, retained, *, index=0, observed_ms=3000):
    return ledger.quarantine_expired(
        index=index,
        occurrence_id=derive_quarantined_occurrence(_POLICY, index),
        observed_ms=observed_ms,
        retained=retained,
    ).witness


def _no_authority(result):
    assert result.notification_authorized is False
    assert result.execution_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.trusted_clock_verified is False
    assert result.consent_verified is False
    assert result.manual_review_required is True


def test_empty_quarantine_is_only_local_unmodified_state(tmp_path: Path):
    _, ledger, before = _setup(tmp_path)
    result = _review(ledger, before)
    assert result.local_state == "UNCHANGED"
    assert result.before_count == result.observed_count == 0
    assert result.locally_present is False
    _no_authority(result)


def test_lost_quarantine_receipt_recovered_without_notification(tmp_path: Path):
    path, ledger, before = _setup(tmp_path)
    _add(ledger, before)
    reopened = DisconnectedScheduleQuarantineLedger(path, policy=_POLICY)
    result = _review(reopened, before)
    assert result.local_state == "LOCALLY_QUARANTINED"
    assert result.before_count == 0 and result.observed_count == 1
    assert result.locally_present is True
    _no_authority(result)


def test_old_quarantine_is_not_a_newly_recorded_row(tmp_path: Path):
    _, ledger, before = _setup(tmp_path)
    tip = _add(ledger, before)
    result = _review(ledger, tip)
    assert result.local_state == "PREEXISTING"
    assert result.before_count == result.observed_count == 1
    _no_authority(result)


def test_advanced_other_slot_cannot_prove_requested_slot(tmp_path: Path):
    _, ledger, before = _setup(tmp_path)
    _add(ledger, before, index=0, observed_ms=3000)
    result = _review(ledger, before, index=1, observed_ms=13000)
    assert result.local_state == "ADVANCED_OTHER"
    assert result.locally_present is False
    assert result.observed_count == 1
    _no_authority(result)


def test_second_quarantine_is_prefix_bound(tmp_path: Path):
    _, ledger, before = _setup(tmp_path)
    first = _add(ledger, before, index=0)
    _add(ledger, first, index=1, observed_ms=13000)
    result = _review(ledger, first, index=1, observed_ms=13000)
    assert result.local_state == "LOCALLY_QUARANTINED"
    assert result.before_count == 1 and result.observed_count == 2
    _no_authority(result)


@pytest.mark.parametrize("before", (
    QuarantineWitness(0, "f" * 64),
    QuarantineWitness(True, "f" * 64),
    QuarantineWitness(1, "f" * 64),
))
def test_invalid_witness_refuses(tmp_path: Path, before):
    _, ledger, _ = _setup(tmp_path)
    with pytest.raises(triage.ScheduleUnknownQuarantineRejected):
        _review(ledger, before)


def test_stale_historical_prefix_refuses(tmp_path: Path):
    _, ledger, before = _setup(tmp_path)
    first = _add(ledger, before)
    _add(ledger, first, index=1, observed_ms=13000)
    with pytest.raises(
        triage.ScheduleUnknownQuarantineRejected, match="retained prefix changed",
    ):
        _review(ledger, QuarantineWitness(1, "f" * 64), index=1, observed_ms=13000)


@pytest.mark.parametrize("value", (2000, 3100, -1, 2**63))
def test_wrong_observed_time_refuses(tmp_path: Path, value: int):
    _, ledger, before = _setup(tmp_path)
    _add(ledger, before)
    with pytest.raises(triage.ScheduleUnknownQuarantineRejected):
        _review(ledger, before, observed_ms=value)


def test_foreign_policy_epoch_not_accepted(tmp_path: Path):
    _, ledger, before = _setup(tmp_path)
    foreign = replace(_POLICY, grace_ms=500)
    with pytest.raises(triage.ScheduleUnknownQuarantineRejected):
        _review(ledger, before, policy=foreign)


@pytest.mark.parametrize("statement", (
    "UPDATE quarantines SET chain_sha256='bad'",
    "UPDATE quarantines SET due_ms=9999",
    "PRAGMA user_version=2",
))
def test_corrupt_chain_schedule_or_schema_refuses(tmp_path: Path, statement: str):
    path, ledger, before = _setup(tmp_path)
    _add(ledger, before)
    with sqlite3.connect(path) as connection:
        connection.execute(statement)
    with pytest.raises(triage.ScheduleUnknownQuarantineRejected):
        _review(ledger, before)


def test_uncommitted_writer_not_mixed_with_read_snapshot(tmp_path: Path):
    path, ledger, before = _setup(tmp_path)
    _add(ledger, before)
    with sqlite3.connect(path, isolation_level=None) as writer:
        writer.execute("BEGIN IMMEDIATE")
        try:
            writer.execute("UPDATE quarantines SET chain_sha256='bad' WHERE seq=1")
            result = _review(ledger, before)
            assert result.local_state == "LOCALLY_QUARANTINED"
            _no_authority(result)
        finally:
            writer.rollback()


@pytest.mark.parametrize("change", ("validate", "open", "notification"))
def test_callback_or_authority_substitution_refused_before_access(
    tmp_path: Path, monkeypatch, change: str,
):
    _, ledger, before = _setup(tmp_path)
    with monkeypatch.context() as patch:
        if change == "validate":
            patch.setattr(
                triage.module, "_validate",
                lambda *args: (_ for _ in ()).throw(AssertionError("forged validator")),
            )
        elif change == "open":
            patch.setattr(
                DisconnectedScheduleQuarantineLedger, "_open",
                lambda *args, **kwargs: (_ for _ in ()).throw(
                    AssertionError("forged SQLite opener")
                ),
            )
        else:
            patch.setattr(
                triage.ScheduleUnknownQuarantineReview,
                "notification_authorized", property(lambda _: True),
            )
        with pytest.raises(
            triage.ScheduleUnknownQuarantineRejected, match="protocol changed",
        ):
            _review(ledger, before)


def test_boolean_index_is_not_a_valid_occurrence_index(tmp_path: Path):
    _, ledger, before = _setup(tmp_path)
    with pytest.raises(triage.ScheduleUnknownQuarantineRejected):
        triage.review_schedule_unknown_quarantine(
            ledger, _POLICY, before, index=True,
            occurrence_id=derive_quarantined_occurrence(_POLICY, 0),
            observed_ms=3000,
        )
