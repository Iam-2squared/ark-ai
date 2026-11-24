"""Run1313: revocation scope digest rejects inexact text before callbacks."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


class _ObservedText(str):
    def __new__(cls, value: str):
        instance = super().__new__(cls, value)
        instance.strip_calls = 0
        return instance

    def strip(self, *args, **kwargs):
        self.strip_calls += 1
        return super().strip(*args, **kwargs)


@pytest.mark.parametrize("field", ("owner_id", "namespace"))
@pytest.mark.parametrize("operation", ("revoke", "assert_not_revoked"))
def test_revocation_rejects_scope_text_subclasses_before_digest_or_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    operation: str,
) -> None:
    owner = _ObservedText("fixture-owner") if field == "owner_id" else "fixture-owner"
    namespace = _ObservedText("private") if field == "namespace" else "private"
    scope = MemoryScope(owner, namespace)
    if isinstance(owner, _ObservedText):
        owner.strip_calls = 0
    if isinstance(namespace, _ObservedText):
        namespace.strip_calls = 0

    ledger = SyntheticContextRevocationLedger(
        tmp_path / f"revocation-exact-scope-{field}-{operation}.sqlite3",
    )
    connect_calls: list[str] = []

    def forbidden_connect(*, readonly: bool):
        connect_calls.append("connect")
        raise AssertionError("inexact scope reached SQLite")

    monkeypatch.setattr(ledger, "_connect", forbidden_connect)
    with pytest.raises(SyntheticContextRevocationRejected, match="exact scope text"):
        if operation == "revoke":
            ledger.revoke(scope, at_ms=100)
        else:
            ledger.assert_not_revoked((scope,))

    assert connect_calls == []
    if isinstance(owner, _ObservedText):
        assert owner.strip_calls == 0
    if isinstance(namespace, _ObservedText):
        assert namespace.strip_calls == 0

    with sqlite3.connect(ledger.path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations",
        ).fetchone() == (0,)
