"""Manual-only pre-action COMMIT-UNKNOWN triage against real SQLite epochs."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.agency.disconnected_atomic_unknown_outcome_review as review
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(seed: str = "a") -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + seed * 64, "bound_" + "b" * 64, "c" * 64)


def _store(tmp_path: Path) -> DisconnectedAtomicPreactionLedger:
    return DisconnectedAtomicPreactionLedger.create(tmp_path / "preaction.sqlite")


def _review(
    store: DisconnectedAtomicPreactionLedger,
    before: AtomicPreactionWitness,
    claim: AtomicIntentClaim,
) -> review.AtomicUnknownOutcomeReview:
    return review.review_atomic_unknown_outcome(store, before, claim)


def _assert_no_authority(result: review.AtomicUnknownOutcomeReview) -> None:
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_effect_verified is False
    assert result.independent_custody_verified is False
    assert result.manual_review_required is True


def test_empty_epoch_is_not_external_absence_evidence(tmp_path: Path) -> None:
    store = _store(tmp_path)
    result = _review(store, genesis_atomic_preaction_witness(), _claim())
    assert result.local_state == "UNCHANGED"
    assert result.before_count == result.observed_count == 0
    assert result.locally_present is False
    _assert_no_authority(result)


def test_lost_receipt_can_be_locally_recorded_but_not_replayed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    before = genesis_atomic_preaction_witness()
    claim = _claim()
    store.reserve(claim, retained=before)
    result = _review(DisconnectedAtomicPreactionLedger(
        tmp_path / "preaction.sqlite",
    ), before, claim)
    assert result.local_state == "LOCALLY_RECORDED"
    assert result.before_count == 0 and result.observed_count == 1
    assert result.locally_present is True
    _assert_no_authority(result)


def test_unrelated_concurrent_commit_does_not_prove_requested_action(tmp_path: Path) -> None:
    store = _store(tmp_path)
    before = genesis_atomic_preaction_witness()
    store.reserve(_claim("d"), retained=before)
    result = _review(store, before, _claim())
    assert result.local_state == "ADVANCED_OTHER"
    assert result.observed_count == 1 and result.locally_present is False
    _assert_no_authority(result)


def test_known_preexisting_occurrence_is_not_new_commit(tmp_path: Path) -> None:
    store = _store(tmp_path)
    claim = _claim()
    retained = store.reserve(claim, retained=genesis_atomic_preaction_witness())
    result = _review(store, retained, claim)
    assert result.local_state == "PREEXISTING"
    assert result.before_count == result.observed_count == 1
    _assert_no_authority(result)


@pytest.mark.parametrize("seed", ("d", "e", "f"))
def test_multiple_unrelated_commits_remain_manual_only(tmp_path: Path, seed: str) -> None:
    store = _store(tmp_path)
    before = genesis_atomic_preaction_witness()
    claim = _claim(seed)
    store.reserve(claim, retained=before)
    result = _review(store, before, _claim())
    assert result.local_state == "ADVANCED_OTHER"
    _assert_no_authority(result)


@pytest.mark.parametrize("before", (
    AtomicPreactionWitness(0, "f" * 64),
    AtomicPreactionWitness(True, "f" * 64),
    AtomicPreactionWitness(1, "f" * 64),
))
def test_invalid_or_unanchored_prefix_refuses(tmp_path: Path, before) -> None:
    store = _store(tmp_path)
    with pytest.raises(review.AtomicUnknownOutcomeRejected):
        _review(store, before, _claim())


def test_retained_nonzero_prefix_must_match_historical_row(tmp_path: Path) -> None:
    store = _store(tmp_path)
    prior = store.reserve(_claim("d"), retained=genesis_atomic_preaction_witness())
    store.reserve(_claim("e"), retained=prior)
    with pytest.raises(
        review.AtomicUnknownOutcomeRejected, match="retained prefix altered",
    ):
        _review(store, AtomicPreactionWitness(1, "f" * 64), _claim())
    result = _review(store, prior, _claim())
    assert result.local_state == "ADVANCED_OTHER"


def test_same_occurrence_different_bound_request_cannot_be_accepted(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    before = genesis_atomic_preaction_witness()
    store.reserve(_claim(), retained=before)
    wrong = AtomicIntentClaim(_claim().occurrence_id, "bound_" + "d" * 64, "c" * 64)
    with pytest.raises(
        review.AtomicUnknownOutcomeRejected, match="identity collision",
    ):
        _review(store, before, wrong)


@pytest.mark.parametrize("statement", (
    "DELETE FROM preaction_audit",
    "UPDATE preaction_audit SET audit_sha256='bad'",
    "UPDATE intents SET chain_sha256='bad'",
    "PRAGMA user_version=2",
))
def test_corrupt_or_incomplete_preaction_audit_refuses(
    tmp_path: Path, statement: str,
) -> None:
    store = _store(tmp_path)
    before = genesis_atomic_preaction_witness()
    store.reserve(_claim(), retained=before)
    with sqlite3.connect(tmp_path / "preaction.sqlite") as connection:
        connection.execute(statement)
    with pytest.raises(review.AtomicUnknownOutcomeRejected):
        _review(store, before, _claim())


def test_uncommitted_sqlite_writer_not_mixed_into_reader_epoch(tmp_path: Path) -> None:
    store = _store(tmp_path)
    before = genesis_atomic_preaction_witness()
    store.reserve(_claim(), retained=before)
    with sqlite3.connect(
        tmp_path / "preaction.sqlite", isolation_level=None,
    ) as writer:
        writer.execute("BEGIN IMMEDIATE")
        try:
            writer.execute("UPDATE intents SET request_sha256='bad' WHERE seq=1")
            result = _review(store, before, _claim())
            assert result.local_state == "LOCALLY_RECORDED"
            _assert_no_authority(result)
        finally:
            writer.rollback()


@pytest.mark.parametrize("replacement", ("scan", "open", "authority"))
def test_original_reviewers_and_denials_checked_before_io(
    tmp_path: Path, monkeypatch, replacement: str,
) -> None:
    store = _store(tmp_path)
    with monkeypatch.context() as patch:
        if replacement == "scan":
            patch.setattr(
                review.ledger_module, "_scan",
                lambda _: (_ for _ in ()).throw(AssertionError("forged scan invoked")),
            )
        elif replacement == "open":
            patch.setattr(
                DisconnectedAtomicPreactionLedger, "_open",
                lambda *args, **kwargs: (_ for _ in ()).throw(
                    AssertionError("forged open invoked")
                ),
            )
        else:
            patch.setattr(
                review.AtomicUnknownOutcomeReview,
                "automatic_replay_authorized", property(lambda _: True),
            )
        with pytest.raises(review.AtomicUnknownOutcomeRejected, match="protocol changed"):
            _review(store, genesis_atomic_preaction_witness(), _claim())


@pytest.mark.parametrize("bad", (
    AtomicIntentClaim("invalid", "bound_" + "b" * 64, "c" * 64),
    AtomicIntentClaim("occ_" + "a" * 64, "bad", "c" * 64),
    AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "bad"),
))
def test_malformed_or_unregistered_synthetic_intent_rejected(
    tmp_path: Path, bad: AtomicIntentClaim,
) -> None:
    store = _store(tmp_path)
    with pytest.raises(review.AtomicUnknownOutcomeRejected):
        _review(store, genesis_atomic_preaction_witness(), bad)
