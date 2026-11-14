"""Actual ARK Memory, ActionAudit and synthetic veto WAL-close regressions.

All stores live under fresh TemporaryDirectory paths. This does not prove
the original intermittent Windows race or allow a failed write to be retried.
"""

from __future__ import annotations

import argparse
import json
import os
import runpy
from pathlib import Path

import pytest

_DIAG = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts"
        / "diagnose_ark_store_wal_last_close.py")
)


@pytest.mark.parametrize("invalid", ["0", "5", "999", "-2", "unbounded"])
def test_disposable_probe_iteration_budget(invalid: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="1..4"):
        _DIAG["bounded_count"](invalid)


@pytest.mark.parametrize("kind", ("memory", "audit", "revocation"))
@pytest.mark.parametrize("keeper", (False, True))
def test_real_ark_schema_recovers_after_final_sqlite_close(
    kind: str, keeper: bool,
) -> None:
    report = _DIAG["probe_ark_store"](kind=kind, keeper=keeper)
    if report["status"] in ("UNSUPPORTED", "NO_WAL", "NO_SHM"):
        pytest.skip("host lacks disposable WAL held-FD probe requirements")
    assert report["status"] == "OK"
    assert report["kind"] == kind
    assert report["keeper"] is keeper
    assert report["before_child_close"] == "SINGLE_LINK"
    assert report["after_final_close"] == "UNLINKED"
    assert report["final_path_absent"] is True
    assert report["cold_read_intact"] is True
    assert report["auto_retry_authorized"] is False
    assert report["real_tool_dispatched"] is False
    assert report["alias_checks_relaxed"] is False
    assert report["user_paths_exported"] is False
    assert report["after_child_close"] == (
        "SINGLE_LINK" if keeper else "UNLINKED"
    )


def test_disposable_probe_rejects_unknown_store_before_looking_at_paths() -> None:
    with pytest.raises(ValueError, match="unknown disposable store"):
        _DIAG["probe_ark_store"](kind="unknown", keeper=False)


@pytest.mark.parametrize("kind", ("memory", "revocation"))
def test_cli_reports_no_disposable_paths_or_authority(capsys, kind: str) -> None:
    if os.name != "posix":
        pytest.skip("POSIX-only WAL last-close probe")
    code = _DIAG["main"](["--kind", kind, "--iterations", "1"])
    payload = capsys.readouterr().out
    assert code == 0
    receipt = json.loads(payload)
    assert receipt["schema_version"] == 1
    assert receipt["automatic_retry_authorized"] is False
    assert receipt["tool_execution_authorized"] is False
    assert receipt["private_paths_exported"] is False
    assert "fixture.sqlite" not in payload
    assert "ark-disposable-wal-" not in payload
