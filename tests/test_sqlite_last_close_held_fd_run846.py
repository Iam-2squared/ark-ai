"""Disposable independent-process WAL/SHM custody evidence; never a permission test.

This probes only TemporaryDirectory-owned SQLite fixtures. It does not
exercise an actual Memory/ActionAudit store, retry unsafe paths, or authorize
relaxing fail-closed sidecar inspection.
"""

from __future__ import annotations

import argparse
import json
import os
import runpy
from pathlib import Path

import pytest

_SCRIPT = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts"
        / "diagnose_sqlite_sidecar_fd_lifecycle.py")
)


@pytest.mark.parametrize("invalid", ["0", "9", "999999", "bad", "-1"])
def test_iteration_budget_is_bounded(invalid: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="1..8"):
        _SCRIPT["_bounded_iterations"](invalid)


@pytest.mark.parametrize("keeper", [False, True])
def test_last_close_sidecar_unlink_is_not_an_authority_grant(keeper: bool) -> None:
    if os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0):
        pytest.skip("POSIX/SQLite WAL held-file-descriptor experiment")
    report = _SCRIPT["probe_disposable_last_close"](keeper=keeper)
    if report["status"] in ("UNSUPPORTED", "NO_WAL", "NO_SHM"):
        pytest.skip("host cannot provide the required disposable WAL/SHM fixture")
    assert report["status"] == "OK"
    assert report["keeper"] is keeper
    assert report["before_child_close_fd"] == "SINGLE_LINK"
    assert report["after_final_close_fd"] == "UNLINKED"
    assert report["after_final_close_name"] == "ABSENT"
    assert report["normal_last_close_unlink_observed"] is True
    assert report["safety_checks_relaxed"] is False
    assert report["real_actions_executed"] is False
    assert report["private_paths_exported"] is False
    if keeper:
        assert report["after_child_close_fd"] == "SINGLE_LINK"
        assert report["after_child_close_name"] == "SINGLE_LINK"
    else:
        assert report["after_child_close_fd"] == "UNLINKED"
        assert report["after_child_close_name"] == "ABSENT"


def test_cli_only_reports_bounded_non_authorizing_categories(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    synthetic = {
        "status": "OK", "keeper": False,
        "normal_last_close_unlink_observed": True,
        "safety_checks_relaxed": False, "real_actions_executed": False,
        "private_paths_exported": False,
    }

    def fake_probe(*, keeper: bool) -> dict[str, object]:
        assert keeper is False
        return dict(synthetic)

    monkeypatch.setitem(
        _SCRIPT["main"].__globals__, "probe_disposable_last_close", fake_probe,
    )
    assert _SCRIPT["main"](["--iterations", "1"]) == 0
    raw = capsys.readouterr().out
    report = json.loads(raw)
    assert report["schema_version"] == 1
    assert report["automatic_retry_authorized"] is False
    assert report["tool_execution_authorized"] is False
    assert report["observations"] == [synthetic]
    assert "specimen.sqlite" not in raw
