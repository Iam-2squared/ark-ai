"""Offline revocation reads/writes preserve source and input across SQL phases.

A durable local privacy veto is never external consent or personal-data erasure.
In particular, a post-COMMIT refusal must not erase a successfully stored veto.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.personal_context_revocation_review as module
from ark.memory.contracts import MemoryScope


def _fixture(tmp_path):
    path = tmp_path / "veto.sqlite"
    ledger = module.SyntheticContextRevocationLedger(path)
    scope = MemoryScope("fixture-user", "private")
    return ledger, path, scope


def _call(ledger, scope, readonly):
    if readonly:
        ledger.assert_not_revoked((scope,))
    else:
        ledger.revoke(scope, at_ms=42)


def _count(path):
    with sqlite3.connect(path) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations",
        ).fetchone()[0]


@pytest.mark.parametrize("readonly", [True, False])
def test_begin_phase_detects_scope_retarget_before_validator_can_restore(
    tmp_path, monkeypatch, readonly,
):
    ledger, path, scope = _fixture(tmp_path)
    opened = []
    original_open = ledger._connect
    original_validate = module._validate
    validated = []

    def validate(conn):
        validated.append(True)
        object.__setattr__(scope, "namespace", "private")
        return original_validate(conn)

    class ConnectionProxy:
        def __init__(self, conn):
            self.conn = conn

        def execute(self, sql, *args):
            value = self.conn.execute(sql, *args)
            if sql.startswith("BEGIN"):
                object.__setattr__(scope, "namespace", "transient")
            return value

        def __getattr__(self, name):
            return getattr(self.conn, name)

    def open_fixture(*, readonly=False):
        conn = original_open(readonly=readonly)
        opened.append(conn)
        return ConnectionProxy(conn)

    monkeypatch.setattr(ledger, "_connect", open_fixture)
    monkeypatch.setattr(module, "_validate", validate)
    with pytest.raises(
        module.SyntheticContextRevocationRejected,
        match="scope changed",
    ):
        _call(ledger, scope, readonly)
    assert validated == []
    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        opened[0].execute("SELECT 1")
    assert _count(path) == 0


@pytest.mark.parametrize("readonly", [True, False])
def test_post_commit_source_drift_fails_closed_without_erasing_veto(
    tmp_path, monkeypatch, readonly,
):
    ledger, path, scope = _fixture(tmp_path)
    original_open = ledger._connect
    commits = []

    class ConnectionProxy:
        def __init__(self, conn):
            self.conn = conn

        def commit(self):
            self.conn.commit()
            commits.append(True)
            ledger.path = Path(str(path))

        def __getattr__(self, name):
            return getattr(self.conn, name)

    def open_fixture(*, readonly=False):
        return ConnectionProxy(original_open(readonly=readonly))

    monkeypatch.setattr(ledger, "_connect", open_fixture)
    with pytest.raises(
        module.SyntheticContextRevocationRejected,
        match="source path changed",
    ):
        _call(ledger, scope, readonly)
    assert commits == [True]
    assert _count(path) == (0 if readonly else 1)
    if not readonly:
        # The original veto survived even though its receipt was rejected.
        recovered = module.SyntheticContextRevocationLedger(path)
        with pytest.raises(
            module.SyntheticContextRevocationRejected, match="scope revoked",
        ):
            recovered.assert_not_revoked((scope,))


def test_normal_veto_write_and_read_are_restart_safe(tmp_path):
    ledger, path, scope = _fixture(tmp_path)
    ledger.assert_not_revoked((scope,))
    digest = ledger.revoke(scope, at_ms=42)
    assert len(digest) == 64
    assert _count(path) == 1
    with pytest.raises(
        module.SyntheticContextRevocationRejected, match="scope revoked",
    ):
        module.SyntheticContextRevocationLedger(path).assert_not_revoked((scope,))
