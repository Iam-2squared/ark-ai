"""Explicit restart veto custody must fail closed if the local DB vanished.

Only disposable synthetic hashes / SQLite are used. No real user context,
consent, deletion, privacy export, account connection, or external action.
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


def test_missing_veto_database_cannot_be_recreated_on_restart(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained_veto.sqlite"
    with pytest.raises(OfflinePrivacyVetoRejected):
        DisconnectedPrivacyVetoLedger(path, require_existing=True)
    assert not path.exists()
    ledger = DisconnectedPrivacyVetoLedger(path)
    receipt = ledger.veto(
        owner_sha256=_OWNER,
        scope_sha256=_SCOPE,
        observed_now_ms=100,
        retained=genesis_privacy_veto_witness(),
    )
    assert receipt.witness is not None
    assert receipt.witness.count == 1
    # Simulate local source loss ONLY in this disposable test directory.
    del ledger
    path.unlink()
    with pytest.raises(OfflinePrivacyVetoRejected):
        DisconnectedPrivacyVetoLedger(path, require_existing=True)
    assert not path.exists()


def test_existing_veto_survives_explicit_restart_without_regrant(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained_veto.sqlite"
    ledger = DisconnectedPrivacyVetoLedger(path)
    receipt = ledger.veto(
        owner_sha256=_OWNER,
        scope_sha256=_SCOPE,
        observed_now_ms=100,
        retained=genesis_privacy_veto_witness(),
    )
    assert receipt.witness is not None
    cold = DisconnectedPrivacyVetoLedger(path, require_existing=True)
    current = cold.witness()
    assert current == receipt.witness
    review = cold.review(
        owner_sha256=_OWNER,
        scope_sha256=_SCOPE,
        retained=current,
    )
    assert review.local_veto_seen is True
    assert review.consent_verified is False
    assert review.context_release_authorized is False
    assert review.user_identity_authenticated is False


def test_preexisting_uninitialized_veto_file_refused_for_restart(
    tmp_path: Path,
) -> None:
    path = tmp_path / "empty.sqlite"
    path.touch()
    with pytest.raises(OfflinePrivacyVetoRejected, match="not initialized"):
        DisconnectedPrivacyVetoLedger(path, require_existing=True)
    assert path.exists()
    # Must not initialize a new empty veto history in the explicit
    # restarter's mistaken existing-file identity.
    assert path.stat().st_size == 0


@pytest.mark.parametrize("bad_mode", (1, 0, "yes", None))
def test_restart_flag_must_be_an_exact_boolean(
    tmp_path: Path, bad_mode: object,
) -> None:
    path = tmp_path / "no-implicit-create.sqlite"
    with pytest.raises(OfflinePrivacyVetoRejected, match="restart mode"):
        DisconnectedPrivacyVetoLedger(path, require_existing=bad_mode)
    assert not path.exists()
