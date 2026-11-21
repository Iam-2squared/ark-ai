"""Run959: privacy veto witnesses are global and scope review is isolated.

A local digest-only fixture is not consent, authenticated identity, data
deletion, independent custody, or cross-store authorization.
"""

from __future__ import annotations

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
)


@pytest.mark.parametrize("first_owner", ("a", "b"))
def test_two_handle_same_scope_revocations_never_reuse_stale_witness(
    tmp_path, first_owner: str,
) -> None:
    path = tmp_path / "synthetic-privacy-veto.sqlite"
    first = DisconnectedPrivacyVetoLedger(path)
    second = DisconnectedPrivacyVetoLedger(path, require_existing=True)
    owners = {"a": "a" * 64, "b": "b" * 64}
    scope = "c" * 64
    other_scope = "d" * 64
    next_owner = "b" if first_owner == "a" else "a"
    genesis = first.witness()
    assert genesis.count == 0
    assert genesis.independent_custody_verified is False

    receipt_a = first.veto(
        owner_sha256=owners[first_owner],
        scope_sha256=scope,
        observed_now_ms=100,
        retained=genesis,
    )
    assert receipt_a.consent_verified is False
    assert receipt_a.deletion_proven is False
    assert receipt_a.context_release_authorized is False
    assert receipt_a.witness is not None
    assert receipt_a.witness.count == 1

    # The other handle may still hold an older complete digest, but cannot
    # use it to claim an unrevoked scope or append another marker.
    with pytest.raises(OfflinePrivacyVetoRejected):
        second.review(
            owner_sha256=owners[next_owner],
            scope_sha256=scope,
            retained=genesis,
        )
    with pytest.raises(OfflinePrivacyVetoRejected):
        second.veto(
            owner_sha256=owners[next_owner],
            scope_sha256=scope,
            observed_now_ms=101,
            retained=genesis,
        )
    retained = second.witness()
    assert retained == receipt_a.witness
    assert retained.count == 1

    seen = second.review(
        owner_sha256=owners[first_owner],
        scope_sha256=scope,
        retained=retained,
    )
    unseen = first.review(
        owner_sha256=owners[next_owner],
        scope_sha256=scope,
        retained=retained,
    )
    assert seen.local_veto_seen is True
    assert unseen.local_veto_seen is False
    for review in (seen, unseen):
        assert review.consent_verified is False
        assert review.context_release_authorized is False
        assert review.user_identity_authenticated is False

    receipt_b = second.veto(
        owner_sha256=owners[next_owner],
        scope_sha256=scope,
        observed_now_ms=101,
        retained=retained,
    )
    assert receipt_b.witness is not None
    assert receipt_b.witness.count == 2
    assert receipt_b.witness.fingerprint != retained.fingerprint
    with pytest.raises(OfflinePrivacyVetoRejected):
        first.review(
            owner_sha256=owners[first_owner],
            scope_sha256=scope,
            retained=retained,
        )

    cold = DisconnectedPrivacyVetoLedger(path, require_existing=True)
    final = cold.witness()
    assert final == receipt_b.witness
    assert final.independent_custody_verified is False
    for owner in owners.values():
        review = cold.review(
            owner_sha256=owner, scope_sha256=scope, retained=final,
        )
        assert review.local_veto_seen is True
        assert review.context_release_authorized is False
    unrelated = cold.review(
        owner_sha256=owners[first_owner],
        scope_sha256=other_scope,
        retained=final,
    )
    assert unrelated.local_veto_seen is False
    assert unrelated.consent_verified is False
    assert unrelated.context_release_authorized is False
