"""Disposable ActionAudit WAL forensics never treat child text as authority."""

from __future__ import annotations

import json
import sqlite3
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts" / "diagnose_audit_sidecar_startup.py"
)


def _load():
    spec = util.spec_from_file_location("ark_audit_sidecar_run829", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()


@pytest.mark.parametrize("raw", ("0", "31", "-1", "bad", "", "10000"))
def test_audit_diagnostic_caps_disposable_iterations(raw: str) -> None:
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        _DIAG._positive_iterations(raw)


@pytest.mark.parametrize(
    "raw",
    (
        '{"status":"AUDITED","status":"AUDITED"}',
        '{"status":"OTHER_ERROR","status":"AUDITED"}',
        '{"status":"AUDITED","extra":"secret"}',
        '{"status":"AUDITED","nested":{"a":1,"a":2}}',
        '{"status":"AUDITED","extra":NaN}',
        '{"status":"AUDITED","extra":Infinity}',
        '{"status":"AUDITED"}{"status":"AUDITED"}',
        '{"status":"SIDECAR_REJECTED","phase":"BOOTSTRAP",'
        '"suffix":"-wal","file_type":"0o120000","link_count":1,'
        '"private":"/tmp/private"}',
        '{"status":"OTHER_ERROR","phase":"APPEND",'
        '"exception_type":"A","detail":"private"}',
        "x" * 4097,
        "",
    ),
)
def test_untrusted_audit_child_output_never_forges_success(raw: str) -> None:
    assert _DIAG._parse_child_reply(raw) == {"status": "INVALID_CHILD_OUTPUT"}


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ('{"status":"AUDITED"}', {"status": "AUDITED"}),
        (
            '{"status":"AUDIT_SCHEMA_REJECTED","phase":"BOOTSTRAP"}',
            {"status": "AUDIT_SCHEMA_REJECTED", "phase": "BOOTSTRAP"},
        ),
        (
            '{"status":"SIDECAR_REJECTED","phase":"APPEND",'
            '"suffix":"-shm","file_type":"0o100000","link_count":0}',
            {
                "status": "SIDECAR_REJECTED", "phase": "APPEND",
                "suffix": "-shm", "file_type": "0o100000", "link_count": 0,
            },
        ),
    ),
)
def test_exact_audit_child_receipt_is_bounded_and_path_free(raw, expected) -> None:
    assert _DIAG._parse_child_reply(raw) == expected
    assert "private" not in json.dumps(expected)


def test_disposable_keeper_preserves_two_audit_appends(tmp_path: Path) -> None:
    path = tmp_path / "audit.sqlite"
    result = _DIAG._probe(path, "sequential", wal_keeper=True)
    assert result == [{"status": "AUDITED"}, {"status": "AUDITED"}]
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT event_id FROM action_events ORDER BY event_id"
        ).fetchall() == [(1,), (2,)]
    assert str(tmp_path) not in json.dumps(result)


def test_audit_diagnostic_cli_emits_only_safe_aggregate(capsys) -> None:
    assert _DIAG.main([
        "--iterations", "1", "--startup-mode", "sequential",
        "--wal-keeper",
    ]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    result = json.loads(captured.out)
    assert result["status_counts"] == {"AUDITED": 2}
    assert result["anomalous_iterations"] == 0
    assert result["wal_keeper"] is True
    assert result["sidecar_metadata_only"] == []
    assert result["private_paths_exported"] is False
    assert result["safety_checks_relaxed"] is False
    assert result["real_actions_executed"] is False
    assert "audit.sqlite" not in captured.out
    assert "ark-disposable-audit-" not in captured.out
