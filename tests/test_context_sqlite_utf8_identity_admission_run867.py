"""Personal Context identifiers are exact ASCII digests, not Unicode widths."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.personal_context_replay_ledger as context


@pytest.mark.parametrize(
    ("field", "width"),
    (
        ("request_id", 71),
        ("owner_digest", 64),
        ("context_digest", 64),
        ("binding_digest", 64),
        ("chain_sha256", 64),
    ),
)
def test_unicode_character_width_cannot_bypass_context_sql_byte_gate(
    tmp_path, field, width,
):
    db = tmp_path / "context.sqlite"
    context.DisconnectedContextReplayLedger(db, create=True)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO context_requests VALUES (?,?,?,?,?,?)",
            (
                1, "ctxreq_" + "a" * 64, "b" * 64,
                "c" * 64, "d" * 64, "e" * 64,
            ),
        )
        # SQLite length(TEXT) reports codepoints, not native UTF-8 bytes.
        conn.execute(
            f"UPDATE context_requests SET {field}=? WHERE seq=1",
            ("界" * width,),
        )
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("BEGIN")

        class NoPrivateIdentifiers:
            def execute(self, sql, *args):
                if sql.startswith(
                    "SELECT seq,request_id,owner_digest,context_digest,"
                ):
                    raise AssertionError("private context identifiers hydrated")
                return conn.execute(sql, *args)

        with pytest.raises(
            context.OfflineContextReplayRejected,
            match="persisted identity width or storage type",
        ):
            context._inspect(NoPrivateIdentifiers())
        conn.rollback()
    assert db.exists()


def test_genesis_context_ledger_still_uses_original_inert_witness(tmp_path):
    db = tmp_path / "context.sqlite"
    store = context.DisconnectedContextReplayLedger(db, create=True)
    original = context.genesis_offline_context_replay_witness()
    assert store.witness() == original
    assert context.DisconnectedContextReplayLedger(db).witness() == original
    assert original.independent_custody_proven is False
