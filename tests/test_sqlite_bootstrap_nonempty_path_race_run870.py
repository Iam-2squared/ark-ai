"""Nonempty SQLite file planted after lexical create preflight is rejected.

Local monkeypatch models a narrow path-to-open gap, not an actual multi-process
race or a proof of atomic directory-handle custody. No records are disclosed.
"""
from __future__ import annotations

import sqlite3

import pytest

import ark.disconnected_schedule_quarantine_ledger as schedule
import ark.personal_context_replay_ledger as personal


@pytest.mark.parametrize("kind", ("personal", "quarantine"))
def test_foreign_schema_planted_after_path_preflight_stays_untouched(
    tmp_path, monkeypatch, kind,
):
    module = personal if kind == "personal" else schedule
    helper = "_check_path" if kind == "personal" else "_path"
    original = getattr(module, helper)
    path = tmp_path / (kind + ".sqlite")
    inserted = []

    def plant_after_preflight(value, *, create):
        safe = original(value, create=create)
        if create:
            with sqlite3.connect(safe) as connection:
                connection.execute("CREATE TABLE foreign_marker(value TEXT)")
                connection.execute("INSERT INTO foreign_marker VALUES('synthetic')")
            inserted.append(True)
        return safe

    with monkeypatch.context() as patch:
        patch.setattr(module, helper, plant_after_preflight)
        if kind == "personal":
            with pytest.raises(
                personal.OfflineContextReplayRejected, match="not empty",
            ):
                personal.DisconnectedContextReplayLedger(path, create=True)
        else:
            policy = schedule.QuarantinePolicy("a" * 64, 1000, 10000, 3, 1000)
            with pytest.raises(
                schedule.ScheduleQuarantineRejected, match="nonempty",
            ):
                schedule.DisconnectedScheduleQuarantineLedger(
                    path, policy=policy, create=True,
                )
    assert inserted == [True]
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT value FROM foreign_marker"
        ).fetchall() == [("synthetic",)]
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)
