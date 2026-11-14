"""Offline proactive attention never bypasses a retained local privacy veto.

Only temporary synthetic SQLite data/hashes are used. A negative revocation
lookup is not consent, human approval, trusted time or notification authority.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

import ark.offline_attention_revocation_review as join
from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    _scope_digest,
)
from ark.proactive_attention_preview import AttentionBudgetPolicy


def _fixture(tmp_path):
    ledger = SyntheticContextRevocationLedger(tmp_path / "synthetic-veto.sqlite")
    owner_scope = MemoryScope("fixture-owner", "synthetic-notes")
    scope_digest = _scope_digest(owner_scope)
    policy = AttentionBudgetPolicy(
        scope_digest, "b" * 64, 100, 2000, 2, True,
    )
    retained = review_revocation_continuity(ledger)
    return ledger, owner_scope, policy, retained


def _review(ledger, retained, policy, *, now=1500):
    return join.review_offline_attention_revocation(
        ledger, retained, policy, (),
        occurrence_sha256="c" * 64, observation_sha256="d" * 64,
        observed_now_ms=now,
    )


def test_nonrevoked_scope_gets_only_a_detached_review(tmp_path):
    ledger, _, policy, retained = _fixture(tmp_path)
    report = _review(ledger, retained, policy)
    again = _review(ledger, retained, policy)
    assert report == again
    assert report.attention_disposition == "REVIEW_ONLY"
    assert report.attention_review_sha256 is not None
    assert report.vetoed is False
    assert report.revocation_count == 0
    assert all(getattr(report, name) is False for name in join._DENIALS)


def test_local_scope_revocation_vetoes_without_attention_receipt(tmp_path):
    ledger, scope, policy, retained = _fixture(tmp_path)
    before = _review(ledger, retained, policy)
    ledger.revoke(scope, at_ms=1200)
    after = _review(ledger, retained, policy)
    assert after.vetoed is True
    assert after.attention_disposition == "LOCAL_REVOCATION_VETO"
    assert after.attention_review_sha256 is None
    assert after.revocation_count == 1
    assert after.review_sha256 != before.review_sha256
    assert all(getattr(after, name) is False for name in join._DENIALS)


def test_foreign_revocation_does_not_claim_grant_for_unrevoked_scope(tmp_path):
    ledger, _, policy, retained = _fixture(tmp_path)
    ledger.revoke(MemoryScope("fixture-owner", "other-namespace"), at_ms=900)
    report = _review(ledger, retained, policy)
    assert report.vetoed is False
    assert report.revocation_count == 1
    assert report.attention_disposition == "REVIEW_ONLY"
    assert report.consent_verified is False


def test_retained_veto_rollback_is_rejected_without_attention(tmp_path):
    ledger, scope, policy, _ = _fixture(tmp_path)
    digest = ledger.revoke(scope, at_ms=1000)
    retained = review_revocation_continuity(ledger)
    # This deliberate destructive edit affects only a disposable test fixture.
    with sqlite3.connect(ledger.path) as conn:
        conn.execute(
            "DELETE FROM synthetic_context_revocations WHERE scope_digest=?",
            (digest,),
        )
    with pytest.raises(join.AttentionRevocationRejected, match="continuity"):
        _review(ledger, retained, policy)


@pytest.mark.parametrize("broken", ("scope", "witness", "time"))
def test_malformed_input_fails_closed_before_sqlite(tmp_path, monkeypatch, broken):
    ledger, _, policy, retained = _fixture(tmp_path)
    called = []

    def forbidden(*_args, **_kwargs):
        called.append("read")
        raise AssertionError("input must fail before SQLite")

    monkeypatch.setattr(ledger, "_connect", forbidden)
    if broken == "scope":
        policy = replace(policy, scope_sha256="bad")
    elif broken == "witness":
        retained = object()
    with pytest.raises(join.AttentionRevocationRejected):
        _review(ledger, retained, policy, now=True if broken == "time" else 1500)
    assert called == []


@pytest.mark.parametrize("name", ("AttentionBudgetPreview", "SyntheticRevocationWitness"))
def test_rebound_dependency_class_is_rejected_before_sqlite(tmp_path, monkeypatch, name):
    ledger, _, policy, retained = _fixture(tmp_path)
    called = []

    def forbidden(*_args, **_kwargs):
        called.append("read")
        raise AssertionError("class mismatch must fail before SQLite")

    monkeypatch.setattr(ledger, "_connect", forbidden)
    source = join.attention if name == "AttentionBudgetPreview" else join.continuity
    monkeypatch.setattr(source, name, object)
    with pytest.raises(join.AttentionRevocationRejected, match="original"):
        _review(ledger, retained, policy)
    assert called == []


def test_review_digest_binds_synthetic_observation_and_time(tmp_path):
    ledger, _, policy, retained = _fixture(tmp_path)
    first = _review(ledger, retained, policy, now=1500)
    second = _review(ledger, retained, policy, now=1501)
    assert first.review_sha256 != second.review_sha256
    assert "fixture-owner" not in repr(first)
    assert first.notification_authorized is second.notification_authorized is False
