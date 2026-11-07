"""No-dispatch Personal Context restart review over synthetic SQLite identities."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

import ark.personal_context_replay_recovery as review
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayWitness,
    genesis_offline_context_replay_witness,
)
from ark.personal_context_request_binding import bind_offline_context_request

_OWNER = "a" * 64
_SCOPE = "b" * 64
_RECORD = "rec_" + "c" * 32


def _binding(index: int):
    payload = "synthetic-only"
    item = OfflineContextFixture(
        _RECORD, _OWNER, _SCOPE, payload,
        hashlib.sha256(payload.encode()).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (item,), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + f"{index:064x}", preview)


def _ledger(tmp_path):
    return DisconnectedContextReplayLedger(
        tmp_path / "context-recovery.db", create=True,
    )


def test_unchanged_genesis_does_not_grant_authority(tmp_path):
    ledger = _ledger(tmp_path)
    old = genesis_offline_context_replay_witness()
    result = review.review_restarted_context_replay(ledger, old)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert (result.retained_count, result.observed_count) == (0, 0)
    assert len(result.comparison_sha256) == 64
    assert not result.historical_prefix_proven
    assert not result.independent_custody_proven
    assert not result.consent_verified
    assert not result.revocation_freshness_verified
    assert not result.context_disclosure_authorized
    assert not result.tool_dispatch_authorized
    assert not result.automatic_replay_authorized
    assert "synthetic-only" not in repr(result)


def test_advanced_history_is_unverified_and_restart_stable(tmp_path):
    ledger = _ledger(tmp_path)
    old = ledger.witness()
    first = ledger.reserve(_binding(1), retained=old).witness
    advanced = review.review_restarted_context_replay(ledger, old)
    assert advanced.status == "ADVANCED_HISTORY_UNVERIFIED"
    assert (advanced.retained_count, advanced.observed_count) == (0, 1)
    reopened = DisconnectedContextReplayLedger(ledger._path)
    unchanged = review.review_restarted_context_replay(reopened, first)
    assert unchanged.status == "UNCHANGED_LOCAL_HISTORY"
    assert unchanged.observed_count == 1
    assert unchanged.comparison_sha256 != advanced.comparison_sha256


def test_comparison_binds_new_append_and_not_just_endpoints(tmp_path):
    ledger = _ledger(tmp_path)
    start = ledger.witness()
    first = ledger.reserve(_binding(1), retained=start).witness
    digest_one = review.review_restarted_context_replay(ledger, start)
    ledger.reserve(_binding(2), retained=first)
    digest_two = review.review_restarted_context_replay(ledger, start)
    assert digest_one.comparison_sha256 != digest_two.comparison_sha256
    assert digest_two.observed_count == 2
    assert digest_two.status == "ADVANCED_HISTORY_UNVERIFIED"


def test_count_regression_denied(tmp_path):
    ledger = _ledger(tmp_path)
    retained = ledger.reserve(
        _binding(1), retained=ledger.witness(),
    ).witness
    other = DisconnectedContextReplayLedger(
        tmp_path / "empty.db", create=True,
    )
    with pytest.raises(review.OfflineContextRecoveryRejected, match="regressed"):
        review.review_restarted_context_replay(other, retained)


def test_same_count_history_change_denied(tmp_path):
    ledger = _ledger(tmp_path)
    retained = ledger.reserve(
        _binding(1), retained=ledger.witness(),
    ).witness
    forged = replace(retained, chain_sha256="f" * 64)
    with pytest.raises(review.OfflineContextRecoveryRejected, match="rewritten"):
        review.review_restarted_context_replay(ledger, forged)


@pytest.mark.parametrize("bad_count", [True, False, -1, 1.0, 513])
def test_nonexact_or_out_of_bounds_retained_count_denied(tmp_path, bad_count):
    ledger = _ledger(tmp_path)
    forged = replace(
        genesis_offline_context_replay_witness(), count=bad_count,
    )
    with pytest.raises(review.OfflineContextRecoveryRejected, match="witness"):
        review.review_restarted_context_replay(ledger, forged)


@pytest.mark.parametrize("bad_sha", ["F" * 64, "f" * 63, True, "0" * 65])
def test_nonexact_retained_digest_denied(tmp_path, bad_sha):
    ledger = _ledger(tmp_path)
    forged = replace(
        genesis_offline_context_replay_witness(), chain_sha256=bad_sha,
    )
    with pytest.raises(review.OfflineContextRecoveryRejected, match="witness"):
        review.review_restarted_context_replay(ledger, forged)


def test_nonexact_ledger_and_witness_types_denied(tmp_path):
    ledger = _ledger(tmp_path)
    retained = genesis_offline_context_replay_witness()

    class SubWitness(OfflineContextReplayWitness):
        pass

    class SubLedger(DisconnectedContextReplayLedger):
        pass

    with pytest.raises(review.OfflineContextRecoveryRejected, match="witness"):
        review.review_restarted_context_replay(ledger, SubWitness(0, retained.chain_sha256))
    with pytest.raises(review.OfflineContextRecoveryRejected, match="ledger"):
        review.review_restarted_context_replay(SubLedger(ledger._path), retained)


def test_mutated_retained_carrier_during_read_denied(tmp_path, monkeypatch):
    ledger = _ledger(tmp_path)
    retained = ledger.witness()
    original = ledger.witness

    def edited():
        current = original()
        object.__setattr__(retained, "count", 1)
        return current

    monkeypatch.setattr(ledger, "witness", edited)
    with pytest.raises(review.OfflineContextRecoveryRejected, match="witness"):
        review.review_restarted_context_replay(ledger, retained)


def test_mutated_ledger_path_during_read_denied(tmp_path, monkeypatch):
    ledger = _ledger(tmp_path)
    retained = ledger.witness()
    original = ledger.witness

    def moved():
        current = original()
        ledger._path = tmp_path / "forged.db"
        return current

    monkeypatch.setattr(ledger, "witness", moved)
    with pytest.raises(review.OfflineContextRecoveryRejected, match="changed"):
        review.review_restarted_context_replay(ledger, retained)


def test_mutated_observed_witness_during_hash_denied(tmp_path, monkeypatch):
    ledger = _ledger(tmp_path)
    old = ledger.witness()
    original = review.json.dumps

    def mutate(*args, **kwargs):
        object.__setattr__(observed, "chain_sha256", "f" * 64)
        return original(*args, **kwargs)

    observed = ledger.witness()
    monkeypatch.setattr(ledger, "witness", lambda: observed)
    monkeypatch.setattr(review.json, "dumps", mutate)
    with pytest.raises(review.OfflineContextRecoveryRejected, match="observed"):
        review.review_restarted_context_replay(ledger, old)


def test_spoofed_constructed_review_denied(tmp_path, monkeypatch):
    ledger = _ledger(tmp_path)
    monkeypatch.setattr(
        review, "OfflineContextRecoveryReview", lambda *args: object(),
    )
    with pytest.raises(review.OfflineContextRecoveryRejected, match="result"):
        review.review_restarted_context_replay(
            ledger, genesis_offline_context_replay_witness(),
        )
