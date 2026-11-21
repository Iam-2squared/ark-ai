"""Cold WAL read mismatches must fail the diagnostic, even without exceptions.

Fresh synthetic stores only. These checks cannot authorize auto-retry, a live
tool, a real approval, paid compute, or any path-custody relaxation.
"""

from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

_DIAG = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "diagnose_ark_store_wal_last_close.py"
    )
)


@pytest.mark.parametrize("kind", ("memory", "audit", "revocation"))
@pytest.mark.parametrize("keeper", (False, True))
def test_silent_cold_read_mismatch_is_never_reported_ok(
    monkeypatch, kind: str, keeper: bool,
) -> None:
    globals_ = _DIAG["probe_ark_store"].__globals__
    constructor_name = {
        "memory": "SQLiteMemoryStore",
        "audit": "SQLiteActionAudit",
        "revocation": "SyntheticContextRevocationLedger",
    }[kind]
    original = globals_[constructor_name]
    constructor_calls = []

    class MissingColdEvidence:
        def get(self, *_args, **_kwargs):
            return None

        def events(self, *_args, **_kwargs):
            return ()

        def assert_not_revoked(self, *_args, **_kwargs):
            return None

    def replace_only_cold_reader(*args, **kwargs):
        constructor_calls.append(True)
        if len(constructor_calls) == 1:
            return original(*args, **kwargs)
        return MissingColdEvidence()

    with monkeypatch.context() as patch:
        patch.setitem(globals_, constructor_name, replace_only_cold_reader)
        report = _DIAG["probe_ark_store"](kind=kind, keeper=keeper)

    if report["status"] in ("NO_WAL", "NO_SHM", "UNSUPPORTED"):
        pytest.skip("disposable WAL held-FD fixture not available")
    assert len(constructor_calls) == 2
    assert report == {
        "status": "COLD_READ_MISMATCH",
        "kind": kind,
        "keeper": keeper,
        "phase": "cold_restart_read",
        "auto_retry_authorized": False,
        "real_tool_dispatched": False,
        "alias_checks_relaxed": False,
        "user_paths_exported": False,
    }
    assert "fixture.sqlite" not in repr(report)
    assert "ark-disposable-wal-" not in repr(report)


def test_cli_treats_silent_evidence_mismatch_as_nonzero(
    monkeypatch, capsys,
) -> None:
    globals_ = _DIAG["main"].__globals__
    seen = []

    def mismatch(**kwargs):
        seen.append(kwargs)
        return {
            "status": "COLD_READ_MISMATCH",
            "kind": kwargs["kind"],
            "keeper": kwargs["keeper"],
            "phase": "cold_restart_read",
        }

    with monkeypatch.context() as patch:
        patch.setitem(globals_, "probe_ark_store", mismatch)
        rc = _DIAG["main"](["--kind", "memory", "--iterations", "1"])
    assert rc == 1
    assert seen == [{"kind": "memory", "keeper": False}]
    report = json.loads(capsys.readouterr().out)
    assert report["observations"][0]["status"] == "COLD_READ_MISMATCH"
    assert report["automatic_retry_authorized"] is False
    assert report["tool_execution_authorized"] is False
    assert report["private_paths_exported"] is False
