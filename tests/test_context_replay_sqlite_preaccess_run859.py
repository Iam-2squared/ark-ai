"""Personal Context replay preaccess regressions on disposable offline stores.

Only hash metadata is stored; no context text, consent, disclosure or effects.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

import ark.personal_context_replay_ledger as module
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayRejected,
)


@pytest.mark.parametrize("where", ("filename", "ancestor"))
@pytest.mark.parametrize("create", (False, True))
def test_nul_rejected_before_context_file_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, where: str, create: bool,
) -> None:
    path = (tmp_path / "context\x00.sqlite" if where == "filename"
            else tmp_path / "private\x00ancestor" / "context.sqlite")
    calls = []

    def unexpected_lstat(self: Path):
        calls.append(self)
        raise AssertionError("private context path reached lstat")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", unexpected_lstat)
        with pytest.raises(OfflineContextReplayRejected, match="exact absolute"):
            DisconnectedContextReplayLedger(path, create=create)
    assert calls == []


@pytest.mark.parametrize("create", (False, True))
def test_encoded_path_and_journal_budget_precede_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, create: bool,
) -> None:
    path = tmp_path / ("界" * 1400 + ".sqlite")
    assert len(str(path)) < 4096
    assert len(os.fsencode(path)) + len(b"-journal") > 4096
    calls = []

    def unexpected_lstat(self: Path):
        calls.append(self)
        raise AssertionError("overlong context path reached lstat")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", unexpected_lstat)
        with pytest.raises(OfflineContextReplayRejected, match="path byte budget"):
            DisconnectedContextReplayLedger(path, create=create)
    assert calls == []


def test_rebound_encoder_cannot_receive_private_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = []

    def injected(value: object) -> bytes:
        seen.append(value)
        return b"forged"

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "fsencode", injected)
        with pytest.raises(OfflineContextReplayRejected, match="path admission changed"):
            DisconnectedContextReplayLedger(tmp_path / "context.sqlite", create=True)
    assert seen == []


class _RejectPrivateDDL:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.attempted_ddl = False

    def execute(self, statement: str):
        if statement.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            self.attempted_ddl = True
            raise AssertionError("private oversized DDL hydrated before SQL preflight")
        return self.conn.execute(statement)


@pytest.mark.parametrize("kind", ("oversized_ddl", "too_many_schema_objects"))
def test_schema_preflight_rejects_before_private_ddl_hydration(
    tmp_path: Path, kind: str,
) -> None:
    path = tmp_path / "context.sqlite"
    DisconnectedContextReplayLedger(path, create=True)
    with sqlite3.connect(path) as conn:
        if kind == "oversized_ddl":
            conn.execute("CREATE VIEW huge_schema AS SELECT '" + ("x" * 9000) + "'")
        else:
            for index in range(12):
                conn.execute(f"CREATE VIEW extra_{index} AS SELECT {index}")
        conn.commit()
        guarded = _RejectPrivateDDL(conn)
        with pytest.raises(OfflineContextReplayRejected, match="schema drift.*preflight"):
            module._schema(guarded)
        assert guarded.attempted_ddl is False


def test_valid_context_replay_cold_restart_preserves_read_only_contract(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.sqlite"
    DisconnectedContextReplayLedger(path, create=True)
    DisconnectedContextReplayLedger(path, create=False)
    assert path.is_file()
