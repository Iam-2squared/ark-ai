"""Synthetic Memory child receipts need actual post-commit SQLite evidence.

No real user database, external execution or trusted authorization evidence.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts" / "diagnose_memory_sidecar_startup.py"
)


def _load():
    spec = util.spec_from_file_location("memory_durable_readback_run832", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()


@pytest.mark.parametrize(
    ("mode", "operation", "expected"),
    (
        ("same-identity", "create", ["CONFLICT", "CREATED"]),
        ("separate-source", "create", ["CREATED", "CREATED"]),
        ("separate-owner", "generation-cas", ["UPDATED", "UPDATED"]),
        ("same-identity", "generation-cas", ["CONFLICT", "UPDATED"]),
    ),
)
def test_both_child_receipts_require_matching_persisted_rows_and_events(
    tmp_path: Path, mode: str, operation: str, expected: list[str],
) -> None:
    path = tmp_path / "memory.sqlite"
    receipts = _DIAG._probe(path, mode, "sequential", operation)
    assert sorted(item["status"] for item in receipts) == expected
    assert _DIAG._verify_disposable_commit(path, mode, operation)
    assert not _DIAG._verify_disposable_commit(path, "unrecognized", operation)
    assert not _DIAG._verify_disposable_commit(path, mode, "dispatch")
    assert str(tmp_path) not in json.dumps(receipts)


@pytest.mark.parametrize("corruption", ("content", "event", "highwater"))
def test_untrusted_child_success_cannot_cover_missing_persisted_evidence(
    tmp_path: Path, corruption: str,
) -> None:
    path = tmp_path / "memory.sqlite"
    receipts = _DIAG._probe(path, "separate-owner", "sequential")
    assert [item["status"] for item in receipts] == ["CREATED", "CREATED"]
    assert _DIAG._verify_disposable_commit(path, "separate-owner", "create")
    with closing(sqlite3.connect(path)) as conn:
        if corruption == "content":
            conn.execute("UPDATE memories SET content='incorrect'")
        elif corruption == "event":
            conn.execute("DELETE FROM memory_events WHERE event_id=2")
        else:
            conn.execute("UPDATE sqlite_sequence SET seq=8 WHERE name='memory_events'")
        conn.commit()
    assert not _DIAG._verify_disposable_commit(path, "separate-owner", "create")


def test_missing_fixture_is_never_created_by_readback(tmp_path: Path) -> None:
    path = tmp_path / "missing.sqlite"
    assert not _DIAG._verify_disposable_commit(path, "same-identity", "create")
    assert not path.exists()


def test_cli_refuses_forged_success_status_without_any_durable_write(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        _DIAG, "_probe",
        lambda *_args, **_kwargs: [
            {"status": "CREATED"}, {"status": "CREATED"},
        ],
    )
    assert _DIAG.main(["--iterations", "1", "--mode", "separate-owner"]) == 1
    captured = capsys.readouterr()
    assert captured.err == ""
    result = json.loads(captured.out)
    assert result["status_counts"] == {"CREATED": 2}
    assert result["anomalous_iterations"] == 1
    assert result["private_paths_exported"] is False
    assert result["safety_checks_relaxed"] is False
    assert "memory.sqlite" not in captured.out
