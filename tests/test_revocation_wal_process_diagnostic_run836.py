"""Fail-closed disposable revocation WAL lifecycle evidence.

Only a synthetic scope and TemporaryDirectory are used. A receipt is not
consent or proof of external deletion; no rejected path is retried.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_revocation_wal_processes.py"


def _load():
    spec = util.spec_from_file_location("revocation_wal_diagnostic_run836", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()


@pytest.mark.parametrize(
    "reply",
    (
        '{"status":"REVOKED","status":"ALREADY","phase":"REVOKE"}',
        '{"status":"REVOKED","phase":"REVOKE","extra":"/private/file"}',
        '{"status":"REVOKED","phase":"REVOKE"}\n{"status":"ALREADY"}',
        '{"status":"REVOKED","phase":"REVOKE","count":NaN}',
        '{"status":"TIMEOUT","phase":"REVOKE"}',
        '{"status":"REVOKED","phase":"UNKNOWN"}',
        '{"status":["REVOKED"],"phase":"REVOKE"}',
        '{"status":"REVOKED","phase":"REVOKE"}' + (" " * 512),
        "null",
    ),
)
def test_child_reply_fail_closed_without_echo(reply: str) -> None:
    assert _DIAG._parse_reply(reply) == {"status": "INVALID_REPLY", "phase": "UNKNOWN"}


@pytest.mark.parametrize(
    ("status", "phase"),
    (
        ("REVOKED", "REVOKE"),
        ("ALREADY", "REVOKE"),
        ("SIDECAR_REFUSED", "BOOTSTRAP"),
        ("OTHER_DENIAL", "BOOTSTRAP"),
        ("OTHER_ERROR", "BOOTSTRAP"),
    ),
)
def test_only_bounded_exact_child_statuses_survive(status: str, phase: str) -> None:
    payload = json.dumps({"status": status, "phase": phase})
    assert _DIAG._parse_reply(payload) == {"status": status, "phase": phase}


def test_disposable_wal_keeper_has_one_winner_and_one_denied_replay(tmp_path: Path) -> None:
    path = tmp_path / "revocation.sqlite"
    replies, durable = _DIAG._probe(path, wal_keeper=True)
    assert sorted(reply["status"] for reply in replies) == ["ALREADY", "REVOKED"]
    assert all(reply["phase"] == "REVOKE" for reply in replies)
    assert durable
    assert _DIAG._verify_row(path)
    assert str(tmp_path) not in json.dumps(replies)


@pytest.mark.parametrize("mutation", ("digest", "clock", "schema"))
def test_durable_readback_denies_corrupted_fixture(tmp_path: Path, mutation: str) -> None:
    path = tmp_path / "revocation.sqlite"
    _, durable = _DIAG._probe(path, wal_keeper=True)
    assert durable
    with closing(sqlite3.connect(path)) as conn:
        if mutation == "digest":
            conn.execute(
                "UPDATE synthetic_context_revocations SET scope_digest=?",
                ("0" * 64,),
            )
        elif mutation == "clock":
            conn.execute("UPDATE synthetic_context_revocations SET revoked_at_ms=3000")
        else:
            conn.execute("CREATE TABLE unauthorized(extra INTEGER)")
        conn.commit()
    assert not _DIAG._verify_row(path)


def test_missing_database_cannot_be_created_by_readback(tmp_path: Path) -> None:
    missing = tmp_path / "missing.sqlite"
    assert not _DIAG._verify_row(missing)
    assert not missing.exists()


def test_cli_reports_ambiguous_sidecar_without_replay_or_path(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def fake_probe(path, *, wal_keeper=False):
        calls.append((path, wal_keeper))
        return (
            [
                {"status": "REVOKED", "phase": "REVOKE"},
                {"status": "SIDECAR_REFUSED", "phase": "REVOKE"},
            ],
            True,
        )

    monkeypatch.setattr(_DIAG, "_probe", fake_probe)
    assert _DIAG.main(["--iterations", "1", "--wal-keeper"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert len(calls) == 1
    assert calls[0][1] is True
    assert report["anomalous_iterations"] == 1
    assert report["status_counts"] == {"REVOKED": 1, "SIDECAR_REFUSED": 1}
    assert report["private_paths_exported"] is False
    assert report["safety_checks_relaxed"] is False
    assert report["automatic_retry"] is False
    assert "revocation.sqlite" not in json.dumps(report)


@pytest.mark.parametrize("arg", ("0", "13", "-1", "1.5", "bad"))
def test_iteration_bounds(arg: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        _DIAG._iterations(arg)
