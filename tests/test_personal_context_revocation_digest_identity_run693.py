"""Synthetic privacy revocation prefixes reject replaced hashing primitives.

Digest equality is only local continuity, not independently authenticated
consent, source provenance or proof of erasure. Synthetic fixtures only.
"""

from __future__ import annotations

import pytest

from ark import personal_context_revocation_continuity_review as continuity
from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("replacement", ("hash", "sha256", "dumps", "json"))
def test_digest_dependency_replacement_fails_before_private_revocation_read(
    tmp_path, monkeypatch, replacement,
):
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocation.sqlite")
    ledger.revoke(MemoryScope("synthetic-owner", "private"), at_ms=100)
    retained = continuity.review_revocation_continuity(ledger)
    assert len(retained.rows) == 1
    used = []
    opened = []

    if replacement == "hash":
        original = continuity._hash

        def replaced_hash(rows):
            used.append("digest callback")
            return original(rows)

        monkeypatch.setattr(continuity, "_hash", replaced_hash)
    elif replacement == "sha256":
        original = continuity.hashlib.sha256

        def replaced_sha(data=b""):
            used.append("SHA callback")
            return original(data)

        monkeypatch.setattr(continuity.hashlib, "sha256", replaced_sha)
    elif replacement == "dumps":
        original = continuity.json.dumps

        def replaced_dump(*args, **kwargs):
            used.append("JSON callback")
            return original(*args, **kwargs)

        monkeypatch.setattr(continuity.json, "dumps", replaced_dump)
    else:
        monkeypatch.setattr(continuity, "json", object())

    def forbidden_private_connection(*args, **kwargs):
        opened.append(True)
        pytest.fail("untrusted digest dependency reached private revocation SQLite")

    monkeypatch.setattr(ledger, "_connect", forbidden_private_connection)
    with pytest.raises(
        SyntheticContextRevocationRejected,
        match="revocation digest implementation changed",
    ):
        continuity.review_revocation_continuity(ledger, retained=retained)
    assert opened == []
    assert used == []


def test_original_revocation_digest_survives_local_restart_only(tmp_path):
    path = tmp_path / "revocation.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    scope = MemoryScope("synthetic-owner", "private")
    before = continuity.review_revocation_continuity(ledger)
    ledger.revoke(scope, at_ms=100)
    after = continuity.review_revocation_continuity(
        SyntheticContextRevocationLedger(path), retained=before,
    )
    assert len(after.rows) == 1
    assert after.witness_id.startswith("rvk_")
    assert after != before
