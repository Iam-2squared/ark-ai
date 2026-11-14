"""Disposable, path-free SQLite race diagnostic contract (no live user DB)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts" / "diagnose_memory_sidecar_startup.py"
)


def _load_disposable_diagnostic():
    # Local import keeps the test's top-level import block simple.
    from importlib import util

    spec = util.spec_from_file_location("ark_memory_sidecar_diag_run824", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load_disposable_diagnostic()

@pytest.mark.parametrize("value", ("0", "31", "-1", "not-a-number", ""))
def test_disposable_diagnostic_refuses_unbounded_iterations(value):
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        _DIAG._positive_bounded_int(value)


@pytest.mark.parametrize("value", ("1", "12", "30"))
def test_disposable_diagnostic_accepts_only_bounded_count(value):
    assert _DIAG._positive_bounded_int(value) == int(value)


@pytest.mark.parametrize(
    ("mode", "expected"),
    (
        ("same-identity", ("CONFLICT", "CREATED")),
        ("separate-owner", ("CREATED", "CREATED")),
        ("separate-namespace", ("CREATED", "CREATED")),
        ("separate-source", ("CREATED", "CREATED")),
    ),
)
def test_ci_equivalent_sequential_bootstrap_then_shared_release(
    tmp_path: Path, mode: str, expected: tuple[str, str],
):
    # Fresh subprocesses, never the caller's DB; each parent owns tmp_path.
    # A real cross-process failure must FAIL, not be retried or suppressed.
    results = _DIAG._probe(tmp_path / "memory.sqlite", mode, "sequential")
    assert len(results) == 2
    assert tuple(sorted(item["status"] for item in results)) == expected
    report = json.dumps(results, sort_keys=True)
    assert str(tmp_path) not in report
    assert "memory.sqlite" not in report
    assert "fixture" not in report


def test_disposable_cli_emits_aggregate_only_without_disk_paths(capsys):
    assert _DIAG.main([
        "--iterations", "1", "--mode", "separate-owner",
        "--startup-mode", "sequential",
    ]) == 0
    output = capsys.readouterr()
    receipt = json.loads(output.out)
    assert output.err == ""
    assert receipt["startup_mode"] == "sequential"
    assert receipt["mode"] == "separate-owner"
    assert receipt["iterations"] == 1
    assert receipt["anomalous_iterations"] == 0
    assert receipt["status_counts"] == {"CREATED": 2}
    assert receipt["sidecar_metadata_only"] == []
    assert receipt["private_paths_exported"] is False
    assert receipt["safety_checks_relaxed"] is False
    assert "ark-disposable-memory-" not in output.out
    assert "memory.sqlite" not in output.out
