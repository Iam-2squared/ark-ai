"""Run1370: the Personal Context revocation guard cannot be replaced.

Synthetic local SQLite only. This is a fail-closed implementation check, not
authenticated consent, trusted storage, erasure, or a downstream-use lease.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.personal_context_revocation_review as revocation
from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("operation", ("constructor", "digest", "revoke", "read"))
def test_replaced_revocation_guard_is_rejected_before_private_store_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    path = tmp_path / f"guard-self-custody-{operation}.sqlite3"
    ledger = SyntheticContextRevocationLedger(path)
    scope = MemoryScope("fixture-owner", "private")
    opened: list[object] = []

    def forbidden_connect(*args: object, **kwargs: object) -> None:
        opened.append((args, kwargs))
        raise AssertionError("replaced revocation guard reached SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(revocation, "_require_original_scope_digest", lambda: None)
        if operation == "constructor":
            patch.setattr(revocation.sqlite3, "connect", forbidden_connect)
            with pytest.raises(
                SyntheticContextRevocationRejected,
                match="revocation scope digest implementation changed",
            ):
                SyntheticContextRevocationLedger(path, require_existing=True)
        else:
            if operation != "digest":
                patch.setattr(
                    ledger,
                    "_connect",
                    lambda **kwargs: forbidden_connect(**kwargs),
                )
            with pytest.raises(
                SyntheticContextRevocationRejected,
                match="revocation scope digest implementation changed",
            ):
                if operation == "digest":
                    revocation._scope_digest(scope)
                elif operation == "revoke":
                    ledger.revoke(scope, at_ms=100)
                else:
                    ledger.assert_not_revoked((scope,))

    assert opened == []
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations",
        ).fetchone() == (0,)
