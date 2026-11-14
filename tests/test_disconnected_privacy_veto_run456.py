"""Synthetic privacy veto is persistent, monotone and never grants consent."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
    OfflinePrivacyVetoWitness,
    genesis_privacy_veto_witness,
)

OWNER = "a" * 64
SCOPE = "b" * 64
OTHER = "c" * 64


def create(tmp_path):
    return DisconnectedPrivacyVetoLedger(tmp_path / "veto.sqlite3")


def test_genesis_and_one_way_veto(tmp_path):
    ledger = create(tmp_path)
    genesis = genesis_privacy_veto_witness()
    assert ledger.witness() == genesis
    before = ledger.review(owner_sha256=OWNER, scope_sha256=SCOPE, retained=genesis)
    assert not before.local_veto_seen
    assert not before.consent_verified
    assert not before.context_release_authorized
    receipt = ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE, observed_now_ms=17, retained=genesis,
    )
    assert receipt.witness.count == 1
    assert not receipt.consent_verified
    assert not receipt.deletion_proven
    assert not receipt.context_release_authorized
    reopened = create(tmp_path)
    review = reopened.review(
        owner_sha256=OWNER, scope_sha256=SCOPE, retained=receipt.witness,
    )
    assert review.local_veto_seen
    assert not review.consent_verified
    assert not review.user_identity_authenticated
    assert not review.context_release_authorized
    assert not receipt.witness.independent_custody_verified
    with pytest.raises(FrozenInstanceError):
        review.local_veto_seen = False


def test_cross_owner_and_scope_isolation(tmp_path):
    ledger = create(tmp_path)
    receipt = ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE, observed_now_ms=18,
        retained=genesis_privacy_veto_witness(),
    )
    for owner, scope, expected in [
        (OWNER, SCOPE, True), (OWNER, OTHER, False), (OTHER, SCOPE, False),
    ]:
        review = ledger.review(
            owner_sha256=owner, scope_sha256=scope, retained=receipt.witness,
        )
        assert review.local_veto_seen is expected
        assert not review.context_release_authorized


def test_duplicate_and_stale_rejected_without_append(tmp_path):
    ledger = create(tmp_path)
    first = ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE, observed_now_ms=18,
        retained=genesis_privacy_veto_witness(),
    )
    with pytest.raises(OfflinePrivacyVetoRejected, match="duplicate"):
        ledger.veto(
            owner_sha256=OWNER, scope_sha256=SCOPE, observed_now_ms=19,
            retained=first.witness,
        )
    with pytest.raises(OfflinePrivacyVetoRejected, match="stale"):
        ledger.veto(
            owner_sha256=OWNER, scope_sha256=OTHER, observed_now_ms=19,
            retained=genesis_privacy_veto_witness(),
        )
    assert ledger.witness() == first.witness


def test_clock_rollback_rejected(tmp_path):
    ledger = create(tmp_path)
    first = ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE, observed_now_ms=200,
        retained=genesis_privacy_veto_witness(),
    )
    with pytest.raises(OfflinePrivacyVetoRejected, match="clock"):
        ledger.veto(
            owner_sha256=OWNER, scope_sha256=OTHER, observed_now_ms=199,
            retained=first.witness,
        )
    assert ledger.witness() == first.witness


@pytest.mark.parametrize("owner,scope,when", [
    (True, SCOPE, 1), (OWNER, False, 1), ("A" * 64, SCOPE, 1),
    (OWNER, "a" * 63, 1), (OWNER, SCOPE, True), (OWNER, SCOPE, -1),
    (OWNER, SCOPE, 2**63), (OWNER, SCOPE, 1.0), (None, SCOPE, 1),
])
def test_invalid_append_rejected(tmp_path, owner, scope, when):
    ledger = create(tmp_path)
    with pytest.raises(OfflinePrivacyVetoRejected):
        ledger.veto(
            owner_sha256=owner, scope_sha256=scope,
            observed_now_ms=when, retained=genesis_privacy_veto_witness(),
        )
    assert ledger.witness() == genesis_privacy_veto_witness()


@pytest.mark.parametrize("witness", [
    None, True, "a" * 64, OfflinePrivacyVetoWitness(True, "a" * 64),
    OfflinePrivacyVetoWitness(-1, "a" * 64),
    OfflinePrivacyVetoWitness(513, "a" * 64),
    OfflinePrivacyVetoWitness(0, "A" * 64),
])
def test_invalid_retained_witness_rejected(tmp_path, witness):
    ledger = create(tmp_path)
    with pytest.raises(OfflinePrivacyVetoRejected):
        ledger.veto(owner_sha256=OWNER, scope_sha256=SCOPE,
                    observed_now_ms=1, retained=witness)
    with pytest.raises(OfflinePrivacyVetoRejected):
        ledger.review(owner_sha256=OWNER, scope_sha256=SCOPE, retained=witness)


def test_two_threads_cas_one_wins(tmp_path):
    path = tmp_path / "veto.sqlite3"
    ledger = DisconnectedPrivacyVetoLedger(path)
    origin = genesis_privacy_veto_witness()

    def attempt(_):
        try:
            return DisconnectedPrivacyVetoLedger(path).veto(
                owner_sha256=OWNER, scope_sha256=SCOPE, observed_now_ms=12, retained=origin,
            )
        except OfflinePrivacyVetoRejected:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(attempt, (0, 1)))
    assert sum(x is not None for x in result) == 1
    assert ledger.witness().count == 1


def test_schema_or_row_tampering_rejected(tmp_path):
    ledger = create(tmp_path)
    with sqlite3.connect(tmp_path / "veto.sqlite3") as conn:
        conn.execute("CREATE TABLE injected(x TEXT)")
    with pytest.raises(OfflinePrivacyVetoRejected, match="schema"):
        ledger.witness()


def test_persisted_noncanonical_row_rejected(tmp_path):
    ledger = create(tmp_path)
    first = ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE, observed_now_ms=10,
        retained=genesis_privacy_veto_witness(),
    )
    with sqlite3.connect(tmp_path / "veto.sqlite3") as conn:
        conn.execute("UPDATE synthetic_privacy_veto SET recorded_at_ms=1.5 WHERE seq=1")
    with pytest.raises(OfflinePrivacyVetoRejected, match="malformed"):
        ledger.witness()
    assert first.witness.count == 1


def test_locally_coherent_rollback_requires_independent_witness(tmp_path):
    ledger = create(tmp_path)
    first = ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE, observed_now_ms=10,
        retained=genesis_privacy_veto_witness(),
    )
    with sqlite3.connect(tmp_path / "veto.sqlite3") as conn:
        conn.execute("DELETE FROM synthetic_privacy_veto")
    assert ledger.witness() == genesis_privacy_veto_witness()
    with pytest.raises(OfflinePrivacyVetoRejected, match="stale"):
        ledger.review(owner_sha256=OWNER, scope_sha256=SCOPE, retained=first.witness)


def test_reopening_deleted_file_fails_without_recreating(tmp_path):
    path = tmp_path / "veto.sqlite3"
    ledger = DisconnectedPrivacyVetoLedger(path)
    path.unlink()
    with pytest.raises(OfflinePrivacyVetoRejected):
        ledger.review(
            owner_sha256=OWNER, scope_sha256=SCOPE,
            retained=genesis_privacy_veto_witness(),
        )
    assert not path.exists()


def test_repr_hides_local_pseudonymous_owner_and_scope(tmp_path):
    receipt = create(tmp_path).veto(
        owner_sha256=OWNER, scope_sha256=SCOPE, observed_now_ms=10,
        retained=genesis_privacy_veto_witness(),
    )
    assert OWNER not in repr(receipt)
    assert SCOPE not in repr(receipt)
    assert receipt.owner_sha256 == OWNER
    assert receipt.scope_sha256 == SCOPE


def test_symlink_and_relative_input_refused(tmp_path):
    create(tmp_path)
    link = tmp_path / "alias.sqlite3"
    link.symlink_to(tmp_path / "veto.sqlite3")
    with pytest.raises(OfflinePrivacyVetoRejected):
        DisconnectedPrivacyVetoLedger(link)
    with pytest.raises(OfflinePrivacyVetoRejected):
        DisconnectedPrivacyVetoLedger("relative.sqlite3")
