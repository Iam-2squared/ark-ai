"""Create-only WRITE slot SQLite admission never trusts a planted foreign schema.

All fixtures are disposable local databases; no real WRITE or consent occurs.
"""
from __future__ import annotations

import sqlite3

import pytest

import ark.agency.disconnected_write_slot_ledger as slots


@pytest.mark.parametrize("kind", ("table", "view"))
def test_post_preflight_foreign_schema_is_rejected_without_modification(
    tmp_path, monkeypatch, kind,
):
    path = tmp_path / "untrusted.sqlite"
    original = slots._check_path
    planted = []

    def plant_after_preflight(value, *, create):
        checked = original(value, create=create)
        if create:
            ddl = (
                "CREATE TABLE foreign_marker(value TEXT)"
                if kind == "table"
                else "CREATE VIEW foreign_marker AS SELECT 'synthetic' AS value"
            )
            with sqlite3.connect(checked) as connection:
                connection.execute(ddl)
            planted.append(True)
        return checked

    with monkeypatch.context() as patch:
        patch.setattr(slots, "_check_path", plant_after_preflight)
        with pytest.raises(
            slots.WriteSlotLedgerRejected, match="nonempty new ledger",
        ):
            slots.DisconnectedWriteSlotLedger(path, create=True)

    assert planted == [True]
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT type FROM sqlite_master WHERE name='foreign_marker'"
        ).fetchall() == [(kind,)]
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE name='synthetic_write_slots'"
        ).fetchone() is None


def test_clean_create_only_slot_bootstrap_remains_compatible(tmp_path):
    path = tmp_path / "fresh.sqlite"
    slots.DisconnectedWriteSlotLedger(path, create=True)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_write_slots"
        ).fetchone() == (0,)
