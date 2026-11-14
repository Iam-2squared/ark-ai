"""Synthetic privacy veto CAS must not depend on mutable witness equality."""

from dataclasses import replace

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
    OfflinePrivacyVetoReview,
    OfflinePrivacyVetoWitness,
)

_OWNER = "a" * 64
_SCOPE = "b" * 64


def _ledger(tmp_path):
    return DisconnectedPrivacyVetoLedger(tmp_path / "veto-fixture.sqlite3")


@pytest.mark.parametrize("operation", ("review", "veto"))
def test_forged_witness_equality_never_masks_stale_cas(
    tmp_path, monkeypatch, operation,
):
    ledger = _ledger(tmp_path)
    old = ledger.witness()
    stale = replace(old, fingerprint="f" * 64)
    monkeypatch.setattr(
        OfflinePrivacyVetoWitness, "__eq__", lambda self, other: True,
    )
    with pytest.raises(OfflinePrivacyVetoRejected, match="stale"):
        if operation == "review":
            ledger.review(
                owner_sha256=_OWNER, scope_sha256=_SCOPE, retained=stale,
            )
        else:
            ledger.veto(
                owner_sha256=_OWNER, scope_sha256=_SCOPE,
                observed_now_ms=1, retained=stale,
            )
    assert ledger.witness().count == 0


def test_forged_witness_inequality_does_not_block_valid_fixture(
    tmp_path, monkeypatch,
):
    ledger = _ledger(tmp_path)
    baseline = ledger.witness()
    monkeypatch.setattr(
        OfflinePrivacyVetoWitness, "__eq__", lambda self, other: False,
    )
    before = ledger.review(
        owner_sha256=_OWNER, scope_sha256=_SCOPE, retained=baseline,
    )
    assert before.local_veto_seen is False
    next_receipt = ledger.veto(
        owner_sha256=_OWNER, scope_sha256=_SCOPE,
        observed_now_ms=1, retained=baseline,
    )
    after = ledger.review(
        owner_sha256=_OWNER, scope_sha256=_SCOPE,
        retained=next_receipt.witness,
    )
    assert after.local_veto_seen is True
    assert after.consent_verified is False


@pytest.mark.parametrize(
    "denial",
    (
        "consent_verified",
        "context_release_authorized",
        "user_identity_authenticated",
    ),
)
def test_false_only_replaced_review_denial_is_not_original(
    tmp_path, monkeypatch, denial,
):
    ledger = _ledger(tmp_path)
    baseline = ledger.witness()
    monkeypatch.setattr(
        OfflinePrivacyVetoReview, denial, property(lambda _self: False),
    )
    with pytest.raises(OfflinePrivacyVetoRejected, match="acquired authority"):
        ledger.review(
            owner_sha256=_OWNER, scope_sha256=_SCOPE, retained=baseline,
        )
    assert ledger.witness().count == 0
