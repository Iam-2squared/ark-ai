"""Disposable WAL diagnosis reports only bounded, content-free failure phases.

These fault injections do not touch a user database, authorize side effects,
or turn an ambiguous revocation into a successful/retryable operation.
"""

import json
import os
import runpy
from pathlib import Path

import pytest

_DIAG = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts"
        / "diagnose_ark_store_wal_last_close.py")
)


@pytest.mark.skipif(
    os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0),
    reason="held descriptor last-close fixture is POSIX-only",
)
def test_schema_setup_failure_exposes_only_a_phase(monkeypatch):
    globals_ = _DIAG["probe_ark_store"].__globals__

    def forbidden(*_args, **_kwargs):
        raise RuntimeError("private-path-must-not-be-exported")

    with monkeypatch.context() as patch:
        patch.setitem(globals_, "SQLiteMemoryStore", forbidden)
        receipt = _DIAG["probe_ark_store"](kind="memory", keeper=False)
    assert receipt == {
        "status": "PROBE_ERROR",
        "kind": "memory",
        "keeper": False,
        "phase": "schema_setup",
    }
    assert "private-path" not in repr(receipt)
    assert "sqlite" not in repr(receipt)


@pytest.mark.skipif(
    os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0),
    reason="held descriptor last-close fixture is POSIX-only",
)
def test_child_start_failure_does_not_leak_paths_or_start_an_action(monkeypatch):
    globals_ = _DIAG["probe_ark_store"].__globals__
    invoked = []

    def forbidden(*args, **kwargs):
        invoked.append((args, kwargs))
        raise OSError("synthetic-child-fault-private-path")

    with monkeypatch.context() as patch:
        patch.setattr(globals_["subprocess"], "Popen", forbidden)
        receipt = _DIAG["probe_ark_store"](kind="memory", keeper=True)
    if receipt["status"] in ("NO_WAL", "NO_SHM"):
        pytest.skip("disposable held-WAL setup unsupported on host")
    assert receipt == {
        "status": "PROBE_ERROR",
        "kind": "memory",
        "keeper": True,
        "phase": "child_start",
    }
    assert len(invoked) == 1
    assert "private-path" not in json.dumps(receipt)
    assert "fixture.sqlite" not in json.dumps(receipt)


def test_cli_error_receipt_preserves_denial_and_hides_fixture_paths(
    monkeypatch, capsys,
):
    globals_ = _DIAG["main"].__globals__

    def synthetic(*, kind, keeper):
        return {
            "status": "PROBE_ERROR",
            "kind": kind,
            "keeper": keeper,
            "phase": "cold_restart",
        }

    with monkeypatch.context() as patch:
        patch.setitem(globals_, "probe_ark_store", synthetic)
        code = _DIAG["main"](["--kind", "memory"])
    report = json.loads(capsys.readouterr().out)
    assert code == 1
    assert report["observations"][0]["phase"] == "cold_restart"
    assert report["automatic_retry_authorized"] is False
    assert report["tool_execution_authorized"] is False
    assert report["private_paths_exported"] is False
    assert "fixture.sqlite" not in json.dumps(report)
