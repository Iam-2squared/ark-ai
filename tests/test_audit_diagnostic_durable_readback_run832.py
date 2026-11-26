"""Synthetic ActionAudit status text must match real local committed events."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts" / "diagnose_audit_sidecar_startup.py"
)


def _load():
    spec = util.spec_from_file_location("audit_durable_readback_run832", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()


def test_readback_checks_all_synthetic_events_not_only_event_ids(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.sqlite"
    assert _DIAG._probe(path, "sequential", wal_keeper=True) == [
        {"status": "AUDITED"}, {"status": "AUDITED"},
    ]
    assert _DIAG._verify_disposable_audit(path)


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("outcome", "an_unrelated_effect"),
        ("tool", "substituted"),
        ("capability", "other"),
        ("arguments_sha256", "0" * 64),
        ("occurred_at_ms", 3333),
    ),
)
def test_durable_audit_data_drift_is_not_covered_by_success_receipts(
    tmp_path: Path, column: str, value: object,
) -> None:
    path = tmp_path / "audit.sqlite"
    assert all(
        item["status"] == "AUDITED"
        for item in _DIAG._probe(path, "sequential", wal_keeper=True)
    )
    assert _DIAG._verify_disposable_audit(path)
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            f"UPDATE action_events SET {column}=? WHERE event_id=1",
            (value,),
        )
        conn.commit()
    assert not _DIAG._verify_disposable_audit(path)


def test_missing_audit_fixture_remains_absent(tmp_path: Path) -> None:
    path = tmp_path / "missing.sqlite"
    assert not _DIAG._verify_disposable_audit(path)
    assert not path.exists()


def test_cli_flags_forged_two_successes_without_rows(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        _DIAG, "_probe",
        lambda *_args, **_kwargs: [
            {"status": "AUDITED"}, {"status": "AUDITED"},
        ],
    )
    assert _DIAG.main(["--iterations", "1", "--wal-keeper"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status_counts"] == {"AUDITED": 2}
    assert result["anomalous_iterations"] == 1
    assert result["private_paths_exported"] is False
    assert result["real_actions_executed"] is False
