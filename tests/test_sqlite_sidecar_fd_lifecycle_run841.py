"""Cross-process, path-free held-SHM FD forensics (disposable SQLite only)."""

from __future__ import annotations

import argparse
import json
import os
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "diagnose_sqlite_sidecar_fd_lifecycle.py"
)
_spec = util.spec_from_file_location("sqlite_fd_lifecycle_run841", _SCRIPT)
assert _spec is not None and _spec.loader is not None
_DIAG = util.module_from_spec(_spec)
_spec.loader.exec_module(_DIAG)


@pytest.mark.parametrize("raw", ("0", "-1", "9", "oops"))
def test_disposable_iteration_budget_refuses_unbounded_runs(raw: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        _DIAG._bounded_iterations(raw)


def test_held_regular_fd_reports_singly_linked_without_contents(tmp_path: Path) -> None:
    specimen = tmp_path / "synthetic-shm"
    specimen.write_bytes(b"private fixture material")
    descriptor = os.open(specimen, os.O_RDONLY)
    try:
        assert _DIAG._descriptor_category(descriptor) == "SINGLE_LINK"
        assert _DIAG._name_category(specimen) == "SINGLE_LINK"
    finally:
        os.close(descriptor)
    assert _DIAG._name_category(tmp_path / "absent-shm") == "ABSENT"


@pytest.mark.parametrize("keeper", (False, True))
def test_independent_child_close_is_path_free_and_deny_only(keeper: bool) -> None:
    observed = _DIAG.probe_disposable_last_close(keeper=keeper)
    if observed["status"] == "UNSUPPORTED":
        pytest.skip("safe held-descriptor probe unsupported on this platform")
    assert observed["status"] == "OK"
    assert observed["keeper"] is keeper
    assert observed["before_child_close_fd"] in ("SINGLE_LINK", "UNLINKED")
    assert observed["after_child_close_fd"] in ("SINGLE_LINK", "UNLINKED")
    assert observed["after_final_close_fd"] in ("SINGLE_LINK", "UNLINKED")
    assert observed["normal_last_close_unlink_observed"] in (False, True)
    assert observed["private_paths_exported"] is False
    assert observed["safety_checks_relaxed"] is False
    assert observed["real_actions_executed"] is False
    assert not any("specimen.sqlite" in str(value) for value in observed.values())


def test_cli_aggregates_only_bounded_categories(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    def fake_probe(*, keeper: bool) -> dict[str, object]:
        calls.append(keeper)
        return {
            "status": "OK", "keeper": keeper,
            "normal_last_close_unlink_observed": True,
            "safety_checks_relaxed": False,
        }

    monkeypatch.setattr(_DIAG, "probe_disposable_last_close", fake_probe)
    assert _DIAG.main(["--keeper", "--iterations", "2"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert calls == [True, True]
    assert report["schema_version"] == 1
    assert report["automatic_retry_authorized"] is False
    assert report["tool_execution_authorized"] is False
    assert len(report["observations"]) == 2


def test_cli_rejects_unavailable_disposable_probe(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        _DIAG, "probe_disposable_last_close",
        lambda *, keeper: {"status": "FIXTURE_ERROR", "keeper": keeper},
    )
    assert _DIAG.main(["--iterations", "1"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["observations"][0]["status"] == "FIXTURE_ERROR"
    assert result["automatic_retry_authorized"] is False
