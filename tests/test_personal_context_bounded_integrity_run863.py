"""Detached Personal Context SQLite integrity checks admit at most two rows.

Uses only a disposable ledger; this cannot establish privacy consent,
provenance, trusted time or authorization to retrieve personal information.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark import personal_context_replay_ledger as context_ledger


class _SyntheticQuickCheck:
    def __init__(self, diagnostics: tuple[str, ...], sizes: list[int]):
        self._diagnostics = diagnostics
        self._sizes = sizes

    def fetchmany(self, size: int):
        self._sizes.append(size)
        assert size == 2
        return [(message,) for message in self._diagnostics[:size]]

    def fetchall(self):
        raise AssertionError("unbounded integrity diagnostics not allowed")


class _Connection:
    def __init__(self, real: sqlite3.Connection, diagnostics: tuple[str, ...]):
        self._real = real
        self._diagnostics = diagnostics
        self.sizes: list[int] = []

    def execute(self, sql: str):
        if sql == "PRAGMA quick_check":
            return _SyntheticQuickCheck(self._diagnostics, self.sizes)
        return self._real.execute(sql)


@pytest.mark.parametrize(
    ("diagnostics", "accept"),
    (
        (("ok",), True),
        (("synthetic-corruption",), False),
        (("ok", "synthetic-second-error"), False),
    ),
)
def test_private_context_schema_denies_extra_quick_check_diagnostics(
    tmp_path: Path, diagnostics: tuple[str, ...], accept: bool,
) -> None:
    path = tmp_path / "private-context-synthetic.sqlite"
    context_ledger.DisconnectedContextReplayLedger(path, create=True)
    with sqlite3.connect(path) as original:
        count = original.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
        guarded = _Connection(original, diagnostics)
        if accept:
            context_ledger._schema(guarded)
        else:
            with pytest.raises(
                context_ledger.OfflineContextReplayRejected,
                match="integrity check failed",
            ):
                context_ledger._schema(guarded)
        assert guarded.sizes == [2]
        after = original.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
        assert after == count
        assert original.execute("PRAGMA quick_check").fetchone() == ("ok",)
