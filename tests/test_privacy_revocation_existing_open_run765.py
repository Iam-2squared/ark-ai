"""Recovery-safe opening of synthetic privacy veto ledgers (offline only).

No record below is consent or a claim of erasure. A replaceable local SQLite
file still requires an independently retained witness to detect rollback.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def test_recovery_open_does_not_bootstrap_missing_veto(tmp_path: Path) -> None:
    missing = tmp_path / "missing-veto.sqlite"
    with pytest.raises(SyntheticContextRevocationRejected, match="missing"):
        SyntheticContextRevocationLedger(missing, require_existing=True)
    assert not missing.exists()
    assert not missing.with_name(missing.name + "-journal").exists()


def test_recovery_preserves_existing_revocations_across_restarts(
    tmp_path: Path,
) -> None:
    path = tmp_path / "veto.sqlite"
    scope = MemoryScope("synthetic-owner", "profile")
    other = MemoryScope("other-owner", "profile")
    first = SyntheticContextRevocationLedger(path)
    first.revoke(scope, at_ms=110)
    retained = review_revocation_continuity(first)

    for _ in range(3):
        reopened = SyntheticContextRevocationLedger(
            path, require_existing=True,
        )
        assert review_revocation_continuity(reopened, retained=retained) == retained
        with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
            reopened.assert_not_revoked((scope,))
        reopened.assert_not_revoked((other,))  # absence is not consent
        with pytest.raises(SyntheticContextRevocationRejected, match="already"):
            reopened.revoke(scope, at_ms=111)
    assert review_revocation_continuity(first) == retained


def test_removed_file_cannot_reinitialize_veto_on_recovery(tmp_path: Path) -> None:
    path = tmp_path / "veto.sqlite"
    scope = MemoryScope("synthetic-owner", "profile")
    original = SyntheticContextRevocationLedger(path)
    original.revoke(scope, at_ms=110)
    path.rename(tmp_path / "offline-veto-backup.sqlite")
    with pytest.raises(SyntheticContextRevocationRejected, match="missing"):
        SyntheticContextRevocationLedger(path, require_existing=True)
    assert not path.exists()
    (tmp_path / "offline-veto-backup.sqlite").rename(path)
    recovered = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        recovered.assert_not_revoked((scope,))


def test_unversioned_file_is_not_bootstrapped_in_recovery_mode(
    tmp_path: Path,
) -> None:
    path = tmp_path / "uninitialized.sqlite"
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)
    with pytest.raises(SyntheticContextRevocationRejected, match="uninitialized"):
        SyntheticContextRevocationLedger(path, require_existing=True)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone() == (0,)


@pytest.mark.parametrize("invalid", [1, 0, None, "yes"])
def test_recovery_flag_must_be_exact_boolean(
    tmp_path: Path, invalid: object,
) -> None:
    path = tmp_path / "flag.sqlite"
    with pytest.raises(TypeError, match="exact boolean"):
        SyntheticContextRevocationLedger(path, require_existing=invalid)
    assert not path.exists()


def test_existing_file_mode_is_not_independent_rollback_proof(
    tmp_path: Path,
) -> None:
    path = tmp_path / "replaceable.sqlite"
    scope = MemoryScope("synthetic-owner", "profile")
    original = SyntheticContextRevocationLedger(path)
    original.revoke(scope, at_ms=110)
    retained = review_revocation_continuity(original)
    # Only this temporary fixture is renamed. A valid but substituted empty
    # ledger can pass local schema checks; detached history still catches it.
    path.rename(tmp_path / "archived-veto.sqlite")
    SyntheticContextRevocationLedger(path)
    recovered = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="history changed"):
        review_revocation_continuity(recovered, retained=retained)
