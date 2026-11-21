"""Synthetic scheduler storage must reject hostile rows before Python hydration.

Disposable in-memory SQLite only. No real schedule, notification, consent,
clock authority, replay, device, user data or backend dispatch.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark import proactive_synthetic_review as proactive


def _row() -> tuple[object, ...]:
    scope, policy, source, observation = ("a" * 64, "b" * 64, "c" * 64, "d" * 64)
    identity = "trigger_" + proactive._hash(
        "ARK-trigger-occurrence-v1", (scope, policy, source, observation),
    )
    return identity, scope, policy, source, observation, 10, 11


def _connect(*, reject_row_hydration: bool) -> sqlite3.Connection:
    class Guarded(sqlite3.Connection):
        def execute(self, statement, parameters=(), /):
            if (
                reject_row_hydration
                and "SELECT trigger_id,scope_digest,policy_digest" in statement
            ):
                raise AssertionError("corrupt SQLite row reached Python hydration")
            return super().execute(statement, parameters)

    conn = sqlite3.connect(":memory:", factory=Guarded)
    conn.execute(proactive._TABLE)
    conn.execute("PRAGMA user_version=1")
    return conn


def _insert(conn: sqlite3.Connection, row: tuple[object, ...]) -> None:
    conn.execute(
        "INSERT INTO synthetic_prepared_triggers VALUES (?,?,?,?,?,?,?)", row,
    )


@pytest.mark.parametrize(
    ("index", "replacement"),
    (
        (0, "trigger_" + "e" * 262_144),
        (1, "s" * 262_144),
        (2, sqlite3.Binary(b"x" * 262_144)),
        (3, "y" * 262_144),
        (4, sqlite3.Binary(b"z" * 262_144)),
        (6, sqlite3.Binary(b"t" * 262_144)),
    ),
    ids=(
        "oversized-trigger", "oversized-scope", "blob-policy",
        "oversized-source", "blob-observation", "blob-prepared-time",
    ),
)
def test_untrusted_sqlite_rows_rejected_without_hydration(index, replacement):
    row = list(_row())
    row[index] = replacement
    with closing(_connect(reject_row_hydration=True)) as conn:
        _insert(conn, tuple(row))
        with pytest.raises(
            proactive.SyntheticTriggerRejected,
            match="persisted trigger row integrity failed",
        ):
            proactive._validate(conn)


def test_bounded_row_count_rejected_without_hydration(monkeypatch):
    with closing(_connect(reject_row_hydration=True)) as conn:
        first = _row()
        second = list(first)
        second[0] = "trigger_" + "e" * 64
        _insert(conn, first)
        _insert(conn, tuple(second))
        monkeypatch.setattr(proactive, "_MAX_PREPARATIONS", 1)
        with pytest.raises(
            proactive.SyntheticTriggerRejected,
            match="trigger fixture review budget exceeded",
        ):
            proactive._validate(conn)


def test_correctly_bound_small_row_remains_valid():
    with closing(_connect(reject_row_hydration=False)) as conn:
        _insert(conn, _row())
        proactive._validate(conn)
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_prepared_triggers"
        ).fetchone() == (1,)
