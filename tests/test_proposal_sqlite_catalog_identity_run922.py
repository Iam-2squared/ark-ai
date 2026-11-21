"""Synthetic proposal SQLite catalog admission before Python schema hydration.

Uses disposable, local fixture databases; no external approval or model change.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_proposal_store as store


class _NoCatalogHydration:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.hydrated = False

    def execute(self, statement: str):
        if statement.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            self.hydrated = True
            pytest.fail("forged proposal catalog materialized in Python")
        return self.connection.execute(statement)


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("name", "a" * 4300),
        ("tbl_name", "b" * 4300),
        ("type", "c" * 4300),
        ("name", "表" * 1400),
    ),
)
def test_oversized_sqlite_catalog_identity_rejected_before_hydration(
    tmp_path, column: str, replacement: str,
) -> None:
    path = tmp_path / "synthetic-proposals.sqlite"
    store.create_disconnected_proposal_store(path)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {column}=? "
            "WHERE name='synthetic_proposal_events'",
            (replacement,),
        )
        guard = _NoCatalogHydration(conn)
        with pytest.raises(
            store.DisconnectedProposalStoreRejected,
            match="schema catalog preflight",
        ):
            store._schema(guard)
        assert guard.hydrated is False


def test_cumulative_proposal_catalog_identity_budget(tmp_path) -> None:
    path = tmp_path / "synthetic-proposals.sqlite"
    store.create_disconnected_proposal_store(path)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?,tbl_name=? "
            "WHERE name='synthetic_proposal_events'",
            ("n" * 2400, "t" * 2400),
        )
        guard = _NoCatalogHydration(conn)
        with pytest.raises(
            store.DisconnectedProposalStoreRejected,
            match="schema catalog preflight",
        ):
            store._schema(guard)
        assert guard.hydrated is False


def test_clean_proposal_genesis_keeps_deny_only_snapshot(tmp_path) -> None:
    path = tmp_path / "synthetic-proposals.sqlite"
    original = store.create_disconnected_proposal_store(path)
    clean = store.inspect_disconnected_proposal_store(
        path, proposal_id="proposal_" + "f" * 64,
    )
    assert clean.witness == original
    assert clean.human_review_authenticated is False
    assert clean.execution_authorized is False
    assert clean.candidate_promotion_authorized is False
