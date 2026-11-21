"""Passive disposable WAL lifecycle observation tests; no real Memory access."""

from __future__ import annotations

import json
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_memory_sidecar_startup.py"


def _load():
    spec = util.spec_from_file_location("memory_lifecycle_run836", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()


def test_snapshot_only_returns_bounded_states_without_filenames(tmp_path: Path) -> None:
    database = tmp_path / "memory.sqlite"
    assert _DIAG._bounded_sidecar_states(database) == {
        "-wal": "absent", "-shm": "absent", "-journal": "absent",
    }
    (tmp_path / "memory.sqlite-wal").write_bytes(b"fixture")
    (tmp_path / "memory.sqlite-shm").mkdir()
    assert _DIAG._bounded_sidecar_states(database) == {
        "-wal": "single", "-shm": "nonregular", "-journal": "absent",
    }


def test_symlink_sidecar_is_classified_without_following_target(tmp_path: Path) -> None:
    database = tmp_path / "memory.sqlite"
    target = tmp_path / "target"
    target.write_bytes(b"fixture")
    link = tmp_path / "memory.sqlite-wal"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable to this test runner")
    assert _DIAG._bounded_sidecar_states(database)["-wal"] == "nonregular"
    assert target.read_bytes() == b"fixture"


def test_opt_in_keeper_observes_disposable_two_process_epochs(tmp_path: Path) -> None:
    database = tmp_path / "memory.sqlite"
    lifecycle = []
    receipts = _DIAG._probe(
        database, "separate-owner", "sequential", wal_keeper=True,
        lifecycle=lifecycle,
    )
    assert sorted(item["status"] for item in receipts) == ["CREATED", "CREATED"]
    assert _DIAG._verify_disposable_commit(database, "separate-owner", "create")
    assert [stage for stage, _ in lifecycle] == [
        "prepared", "ready", "child-exit-0", "child-exit-1", "closed",
    ]
    assert all(set(states) == {"-wal", "-shm", "-journal"} for _, states in lifecycle)
    assert str(tmp_path) not in json.dumps(lifecycle)


def test_cli_opt_in_aggregates_only_bounded_lifecycle_categories(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []

    def fake_probe(path, *_args, wal_keeper=False, lifecycle=None):
        calls.append((path, wal_keeper))
        assert lifecycle is not None
        lifecycle.append(("prepared", {"-wal": "single", "-shm": "absent"}))
        return [{"status": "CREATED"}, {"status": "CREATED"}]

    monkeypatch.setattr(_DIAG, "_probe", fake_probe)
    monkeypatch.setattr(_DIAG, "_verify_disposable_commit", lambda *_args: True)
    assert _DIAG.main([
        "--iterations", "1", "--mode", "separate-owner",
        "--lifecycle-snapshots",
    ]) == 0
    report = json.loads(capsys.readouterr().out)
    assert len(calls) == 1
    assert report["anomalous_iterations"] == 0
    assert report["lifecycle_sidecar_counts"] == [
        {"stage": "prepared", "suffix": "-shm", "state": "absent", "count": 1},
        {"stage": "prepared", "suffix": "-wal", "state": "single", "count": 1},
    ]
    assert report["private_paths_exported"] is False
    assert report["safety_checks_relaxed"] is False
    assert "memory.sqlite" not in json.dumps(report)


def test_cli_default_has_no_sidecar_probe(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_probe(path, *_args, wal_keeper=False, lifecycle=None):
        assert lifecycle is None
        return [{"status": "CREATED"}, {"status": "CREATED"}]

    monkeypatch.setattr(_DIAG, "_probe", fake_probe)
    monkeypatch.setattr(_DIAG, "_verify_disposable_commit", lambda *_args: True)
    assert _DIAG.main(["--iterations", "1", "--mode", "separate-owner"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["lifecycle_sidecar_counts"] == []
