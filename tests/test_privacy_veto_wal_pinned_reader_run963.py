"""Run963: a historical WAL reader cannot reauthorize revoked local context.

All owner/scope SHA identifiers are synthetic. The local SQLite fixture
and its digest chain never prove real consent, deletion, or external custody.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
)


@pytest.mark.parametrize("checkpoint", ("PASSIVE", "FULL", "RESTART", "TRUNCATE"))
@pytest.mark.parametrize("two_owners", (False, True))
def test_pinned_reader_cannot_resurrect_veto_after_wal_checkpoint(
    tmp_path, checkpoint: str, two_owners: bool,
) -> None:
    path = tmp_path / "synthetic-wal-revocations.sqlite3"
    scope = "c" * 64
    owners = ("a" * 64, "b" * 64)
    fresh = DisconnectedPrivacyVetoLedger(path)
    genesis = fresh.witness()
    assert genesis.count == 0
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)

    with closing(sqlite3.connect(path, isolation_level=None, timeout=10)) as reader:
        reader.execute("BEGIN")
        assert reader.execute(
            "SELECT COUNT(*) FROM synthetic_privacy_veto"
        ).fetchone() == (0,)

        first = DisconnectedPrivacyVetoLedger(path, require_existing=True)
        receipt = first.veto(
            owner_sha256=owners[0],
            scope_sha256=scope,
            observed_now_ms=100,
            retained=genesis,
        )
        assert receipt.witness is not None
        current = receipt.witness
        if two_owners:
            receipt = first.veto(
                owner_sha256=owners[1],
                scope_sha256=scope,
                observed_now_ms=101,
                retained=current,
            )
            assert receipt.witness is not None
            current = receipt.witness

        # A pinned reader sees old bytes, but cannot transfer that snapshot
        # into an opt-in privacy write or review on a separate connection.
        assert reader.execute(
            "SELECT COUNT(*) FROM synthetic_privacy_veto"
        ).fetchone() == (0,)
        with pytest.raises(OfflinePrivacyVetoRejected, match="stale"):
            first.veto(
                owner_sha256="d" * 64,
                scope_sha256=scope,
                observed_now_ms=102,
                retained=genesis,
            )
        with pytest.raises(OfflinePrivacyVetoRejected, match="stale"):
            first.review(
                owner_sha256=owners[0],
                scope_sha256=scope,
                retained=genesis,
            )
        reader.execute("ROLLBACK")

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"PRAGMA wal_checkpoint({checkpoint})"
        ).fetchone()[0] == 0
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)

    cold = DisconnectedPrivacyVetoLedger(path, require_existing=True)
    assert cold.witness() == current
    assert current.count == (2 if two_owners else 1)
    assert current.independent_custody_verified is False
    for owner, expected in ((owners[0], True), (owners[1], two_owners)):
        review = cold.review(
            owner_sha256=owner,
            scope_sha256=scope,
            retained=current,
        )
        assert review.local_veto_seen is expected
        assert review.consent_verified is False
        assert review.context_release_authorized is False
        assert review.user_identity_authenticated is False
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT seq FROM synthetic_privacy_veto ORDER BY seq"
        ).fetchall() == [(index,) for index in range(1, current.count + 1)]
