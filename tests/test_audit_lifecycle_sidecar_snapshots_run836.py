"""Disposable ActionAudit WAL process observations: local-only, no tool execution."""

from __future__ import annotations

import json
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_audit_sidecar_startup.py"


def _load():
    spec = util.spec_from_file_location("audit_lifecycle_run836", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()


def test_audit_sidecar_states_are_bounded_and_path_free(tmp_path: Path) -> None:
    database = tmp_path / "audit.sqlite"
    assert _DIAG._audit_sidecar_states(database) == {
        "-wal": "absent", "-shm": "absent", "-journal": "absent",
    }
    (tmp_path / "audit.sqlite-wal").write_bytes(b"fixture")
    (tmp_path / "audit.sqlite-shm").mkdir()
    assert _DIAG._audit_sidecar_states(database) == {
        "-wal": "single", "-shm": "nonregular", "-journal": "absent",
    }


def test_audit_symlink_never_dereferenced(tmp_path: Path) -> None:
    database = tmp_path / "audit.sqlite"
    target = tmp_path / "target"
    target.write_bytes(b"fixture")
    try:
        (tmp_path / "audit.sqlite-journal").symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    assert _DIAG._audit_sidecar_states(database)["-journal"] == "nonregular"
    assert target.read_bytes() == b"fixture"


def test_keeper_retains_disposable_audit_wal_epochs(tmp_path: Path) -> None:
    database = tmp_path / "audit.sqlite"
    lifecycle = []
    results = _DIAG._probe(database, "sequential", wal_keeper=True, lifecycle=lifecycle)
    assert [item["status"] for item in results] == ["AUDITED", "AUDITED"]
    assert _DIAG._verify_disposable_audit(database)
    assert [stage for stage, _ in lifecycle] == [
        "prepared", "ready", "child-exit-0", "child-exit-1", "closed",
    ]
    assert all(set(states) == {"-wal", "-shm", "-journal"} for _, states in lifecycle)
    assert str(tmp_path) not in json.dumps(lifecycle)


def test_opt_in_cli_emits_only_aggregate_states(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    def fake_probe(path, startup_mode, *, wal_keeper=False, lifecycle=None):
        calls.append((path, startup_mode, wal_keeper))
        assert lifecycle is not None
        lifecycle.append(("ready", {"-shm": "single", "-wal": "absent"}))
        return [{"status": "AUDITED"}, {"status": "AUDITED"}]

    monkeypatch.setattr(_DIAG, "_probe", fake_probe)
    monkeypatch.setattr(_DIAG, "_verify_disposable_audit", lambda *_args: True)
    assert _DIAG.main(["--iterations", "1", "--lifecycle-snapshots"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert len(calls) == 1
    assert report["anomalous_iterations"] == 0
    assert report["lifecycle_sidecar_counts"] == [
        {"stage": "ready", "suffix": "-shm", "state": "single", "count": 1},
        {"stage": "ready", "suffix": "-wal", "state": "absent", "count": 1},
    ]
    assert report["private_paths_exported"] is False
    assert report["real_actions_executed"] is False
    assert report["safety_checks_relaxed"] is False
    assert "audit.sqlite" not in json.dumps(report)


def test_default_audit_diagnostic_does_not_sample_lifecycle(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_probe(path, startup_mode, *, wal_keeper=False, lifecycle=None):
        assert lifecycle is None
        return [{"status": "AUDITED"}, {"status": "AUDITED"}]

    monkeypatch.setattr(_DIAG, "_probe", fake_probe)
    monkeypatch.setattr(_DIAG, "_verify_disposable_audit", lambda *_args: True)
    assert _DIAG.main(["--iterations", "1"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["lifecycle_sidecar_counts"] == []
