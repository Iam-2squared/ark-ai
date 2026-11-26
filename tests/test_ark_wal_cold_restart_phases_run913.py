"""Disposable WAL cold-restart failures are path-free and phase-specific.

Fixtures create and remove their own temporary SQLite databases. Neither
construct nor read failure proves retry/repair/external-action authority.
"""

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
    reason="held descriptor WAL fixture is POSIX-only",
)
@pytest.mark.parametrize(
    ("kind", "constructor"), (
        ("memory", "SQLiteMemoryStore"),
        ("audit", "SQLiteActionAudit"),
    ),
)
@pytest.mark.parametrize("failure_phase", ("construct", "read"))
def test_cold_restart_failure_phase_refuses_without_paths(
    monkeypatch, kind, constructor, failure_phase,
):
    globals_ = _DIAG["probe_ark_store"].__globals__
    original = globals_[constructor]
    calls = []

    class BrokenColdRead:
        def get(self, *_args, **_kwargs):
            raise OSError("private-fixture-read-path")

        def events(self, *_args, **_kwargs):
            raise OSError("private-fixture-read-path")

    def injected_constructor(*args, **kwargs):
        calls.append(True)
        if len(calls) == 1:
            return original(*args, **kwargs)
        if failure_phase == "construct":
            raise OSError("private-fixture-constructor-path")
        return BrokenColdRead()

    with monkeypatch.context() as patch:
        patch.setitem(globals_, constructor, injected_constructor)
        result = _DIAG["probe_ark_store"](kind=kind, keeper=False)
    if result["status"] in ("NO_WAL", "NO_SHM"):
        pytest.skip("temporary held-WAL setup unsupported on this host")
    assert len(calls) == 2
    assert result == {
        "status": "PROBE_ERROR",
        "kind": kind,
        "keeper": False,
        "phase": "cold_restart_" + failure_phase,
    }
    assert "private-fixture" not in repr(result)
    assert "fixture.sqlite" not in repr(result)
