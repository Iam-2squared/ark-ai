"""Cold restart alone cannot authenticate a replacement valid privacy-veto DB.

All databases live under pytest's disposable temp directory. The caller must
retain the original witness separately: an ordinary valid replacement source
does not carry proof of prior revocations, and nothing here grants consent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
    genesis_privacy_veto_witness,
)

_OWNER = "a" * 64
_SCOPE = "b" * 64
_DIFFERENT_SCOPE = "c" * 64


@pytest.mark.parametrize("replacement_with_one_unrelated_veto", (False, True))
def test_valid_replacement_database_cannot_satisfy_retained_veto_history(
    tmp_path: Path, replacement_with_one_unrelated_veto: bool,
) -> None:
    original_path = tmp_path / "veto.sqlite"
    original = DisconnectedPrivacyVetoLedger(original_path)
    receipt = original.veto(
        owner_sha256=_OWNER,
        scope_sha256=_SCOPE,
        observed_now_ms=100,
        retained=genesis_privacy_veto_witness(),
    )
    assert receipt.witness is not None
    assert receipt.witness.count == 1

    # Independently initialized SQLite source is structurally valid but has
    # either no revocations or an unrelated one with the SAME row count.
    replacement_path = tmp_path / "unrelated.sqlite"
    replacement = DisconnectedPrivacyVetoLedger(replacement_path)
    if replacement_with_one_unrelated_veto:
        replacement.veto(
            owner_sha256=_OWNER,
            scope_sha256=_DIFFERENT_SCOPE,
            observed_now_ms=100,
            retained=genesis_privacy_veto_witness(),
        )
    assert replacement.witness() != receipt.witness

    # This is a simulated local replacement of a DISPOSABLE fixture only.
    del original, replacement
    original_path.unlink()
    replacement_path.rename(original_path)
    cold = DisconnectedPrivacyVetoLedger(original_path, require_existing=True)
    with pytest.raises(
        OfflinePrivacyVetoRejected, match="stale or rewritten veto evidence",
    ):
        cold.review(
            owner_sha256=_OWNER,
            scope_sha256=_SCOPE,
            retained=receipt.witness,
        )

    # A fresh local witness from the replacement has no independent custody:
    # the absence of the old veto is NOT authenticated consent or safe reuse.
    local_only = cold.review(
        owner_sha256=_OWNER,
        scope_sha256=_SCOPE,
        retained=cold.witness(),
    )
    assert local_only.local_veto_seen is False
    assert local_only.consent_verified is False
    assert local_only.context_release_authorized is False
    assert local_only.user_identity_authenticated is False
