"""Run1380: simultaneous continuity-guard alias replacement is denied."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.personal_context_revocation_continuity_review as continuity
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def test_simultaneous_guard_and_alias_replacement_is_denied_before_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = SyntheticContextRevocationLedger(
        tmp_path / "continuity-dual-alias-custody.sqlite3",
    )
    connection_attempts: list[bool] = []
    replacement_calls: list[bool] = []

    def forbidden_connect(*_args: object, **_kwargs: object) -> None:
        connection_attempts.append(True)
        raise AssertionError("replaced continuity guard reached SQLite")

    def replacement_guard() -> None:
        replacement_calls.append(True)

    monkeypatch.setattr(ledger, "_connect", forbidden_connect)
    monkeypatch.setattr(
        continuity, "_require_original_witness_carrier", replacement_guard,
    )
    monkeypatch.setattr(
        continuity, "_ORIGINAL_WITNESS_GUARD", replacement_guard,
    )

    with pytest.raises(
        SyntheticContextRevocationRejected,
        match="revocation digest implementation changed",
    ):
        continuity.review_revocation_continuity(ledger)

    assert replacement_calls == []
    assert connection_attempts == []
