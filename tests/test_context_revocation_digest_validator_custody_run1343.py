"""Run1343: revocation digest and schema validator identity are pinned.

Only synthetic local SQLite and exact MemoryScope fixtures are used. This does
not establish authenticated consent or trusted storage.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.personal_context_revocation_review as revocation
from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("operation", ("revoke", "assert_not_revoked"))
def test_scope_digest_replacement_is_denied_before_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch, operation: str,
) -> None:
    ledger = SyntheticContextRevocationLedger(tmp_path / "scope-digest.sqlite3")
    scope = MemoryScope("fixture-owner", "private")
    connect_calls: list[str] = []

    def forbidden_connect(*, readonly: bool):
        connect_calls.append("connect")
        raise AssertionError("replaced scope digest reached SQLite")

    monkeypatch.setattr(ledger, "_connect", forbidden_connect)
    monkeypatch.setattr(revocation, "_scope_digest", lambda _scope: "0" * 64)

    with pytest.raises(
        SyntheticContextRevocationRejected,
        match="revocation scope digest implementation changed",
    ):
        if operation == "revoke":
            ledger.revoke(scope, at_ms=100)
        else:
            ledger.assert_not_revoked((scope,))

    assert connect_calls == []
    with sqlite3.connect(ledger.path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations",
        ).fetchone() == (0,)


@pytest.mark.parametrize("operation", ("constructor", "revoke", "assert_not_revoked"))
def test_schema_validator_replacement_is_denied_before_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch, operation: str,
) -> None:
    path = tmp_path / "schema-validator.sqlite3"
    ledger = SyntheticContextRevocationLedger(path)
    scope = MemoryScope("fixture-owner", "private")
    connect_calls: list[str] = []

    def forbidden_connect(*_args, **_kwargs):
        connect_calls.append("connect")
        raise AssertionError("replaced schema validator reached SQLite")

    monkeypatch.setattr(revocation, "_validate", lambda _connection: None)
    if operation == "constructor":
        with monkeypatch.context() as patch:
            patch.setattr(revocation.sqlite3, "connect", forbidden_connect)
            with pytest.raises(
                SyntheticContextRevocationRejected,
                match="revocation scope digest implementation changed",
            ):
                SyntheticContextRevocationLedger(path, require_existing=True)
    else:
        monkeypatch.setattr(ledger, "_connect", forbidden_connect)
        with pytest.raises(
            SyntheticContextRevocationRejected,
            match="revocation scope digest implementation changed",
        ):
            if operation == "revoke":
                ledger.revoke(scope, at_ms=100)
            else:
                ledger.assert_not_revoked((scope,))

    assert connect_calls == []
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations",
        ).fetchone() == (0,)
