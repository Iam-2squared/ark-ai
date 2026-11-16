"""Disposable revocation WAL readback bounds catalog bytes before hydration.

Malformed synthetic catalog results cannot trigger a revocation-table read.
No private paths, live user database, automatic replay or external actions.
"""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

_DIAG = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "diagnose_revocation_wal_processes.py"
    )
)


@pytest.mark.parametrize(
    "catalog",
    (
        None, (2,), (0, 0), (1, 0), (3, 0),
        (2, 4097), (2, -1), (2, True), [2, 10],
    ),
)
def test_malformed_catalog_never_reaches_private_row_scan(
    monkeypatch, tmp_path: Path, catalog: object,
) -> None:
    db = tmp_path / "disposable-readback.sqlite"
    db.touch()
    namespace = _DIAG["_verify_row"].__globals__
    queried = []
    closed = []

    class Cursor:
        def __init__(self, row: object) -> None:
            self.row = row

        def fetchone(self):
            return self.row

    class FakeConnection:
        def execute(self, query: str) -> Cursor:
            queried.append(query)
            if query == "PRAGMA query_only=ON" or query == "BEGIN":
                return Cursor(None)
            if query == "PRAGMA user_version":
                return Cursor((1,))
            if "FROM sqlite_master" in query:
                if "SELECT COUNT(*)" in query:
                    return Cursor(catalog)
                raise AssertionError("unbounded catalog hydration")
            raise AssertionError("private row read before catalog preflight")

        def close(self) -> None:
            closed.append(True)

    with monkeypatch.context() as patch:
        patch.setattr(
            namespace["sqlite3"], "connect",
            lambda *_args, **_kwargs: FakeConnection(),
        )
        assert _DIAG["_verify_row"](db) is False

    assert len([q for q in queried if "SELECT COUNT(*)" in q]) == 1
    assert closed == [True]


def test_valid_disposable_revocation_oracle_survives_prehydration(tmp_path: Path) -> None:
    from ark.memory import MemoryScope
    from ark.personal_context_revocation_review import SyntheticContextRevocationLedger

    db = tmp_path / "one-synthetic-veto.sqlite"
    ledger = SyntheticContextRevocationLedger(db)
    ledger.revoke(MemoryScope("synthetic-diagnostic", "profile"), at_ms=2000)
    assert _DIAG["_verify_row"](db) is True
