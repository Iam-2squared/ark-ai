"""Bound SQLite quick-check diagnostics before untrusted startup schema hydration.

Only disposable Memory and ActionAudit v1 fixtures are touched. These synthetic
rows are not corruption proof, storage authentication, consent or tool authority.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.agency import audit as audit_module
from ark.memory import sqlite_store as memory_module


class _QuickCheckCursor:
    def __init__(self, rows: tuple[tuple[str, ...], ...], sizes: list[int]):
        self._rows = rows
        self._sizes = sizes

    def fetchmany(self, size: int):
        self._sizes.append(size)
        assert size == 2, "quick_check must admit at most two diagnostics"
        return self._rows[:size]

    def fetchall(self):
        raise AssertionError("unbounded quick_check result hydration is forbidden")


class _QuickCheckConnection:
    def __init__(self, real: sqlite3.Connection, rows: tuple[tuple[str, ...], ...]):
        self._real = real
        self._rows = rows
        self.read_sizes: list[int] = []

    def execute(self, sql: str):
        if sql == "PRAGMA quick_check":
            return _QuickCheckCursor(self._rows, self.read_sizes)
        return self._real.execute(sql)


@pytest.mark.parametrize("kind", ("memory", "audit"))
@pytest.mark.parametrize(
    ("diagnostics", "allowed"),
    (
        (("ok",), True),
        (("synthetic-corruption",), False),
        (("ok", "synthetic-secondary-diagnostic"), False),
        (("synthetic-corruption", "synthetic-secondary-diagnostic"), False),
    ),
)
def test_bounded_quick_check_rejects_extra_or_bad_diagnostics(
    tmp_path: Path, kind: str, diagnostics: tuple[str, ...], allowed: bool,
) -> None:
    path = tmp_path / "synthetic-schema.sqlite"
    if kind == "memory":
        memory_module.SQLiteMemoryStore(path, clock_ms=lambda: 100)
        validate = memory_module._validate_v1_schema
        rejected = memory_module.MemorySchemaError
    else:
        audit_module.SQLiteActionAudit(path, clock_ms=lambda: 100)
        validate = audit_module._validate_v1_schema
        rejected = audit_module.ActionAuditSchemaError

    with sqlite3.connect(path) as original:
        before = original.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
        synthetic_rows = tuple((message,) for message in diagnostics)
        guarded = _QuickCheckConnection(original, synthetic_rows)
        if allowed:
            validate(guarded)
        else:
            with pytest.raises(rejected, match="quick_check"):
                validate(guarded)
        assert guarded.read_sizes == [2]
        after = original.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
        assert after == before
        assert original.execute("PRAGMA quick_check").fetchone() == ("ok",)
