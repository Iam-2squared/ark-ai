"""Run1302: V3 preflight report output is bounded and path-custody checked.

Only synthetic temporary paths and byte payloads are used. No GPU, torch,
model loading, Candidate, or preflight backend is invoked.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.learning import training_cli as cli


def test_new_preflight_report_is_created_with_exact_payload(tmp_path: Path) -> None:
    path = tmp_path / "reports" / "preflight.json"
    path.parent.mkdir()
    payload = b'{"synthetic":"preflight-report"}'

    cli._write_new_preflight_report(path, payload)

    assert path.read_bytes() == payload
    assert path.stat().st_nlink == 1


def test_existing_leaf_is_denied_before_open(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "preflight.json"
    path.write_bytes(b"existing")
    calls = []

    def forbidden_open(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("existing report leaf must be denied before open")

    monkeypatch.setattr(cli.os, "open", forbidden_open)
    with pytest.raises(RuntimeError, match="must be a new file"):
        cli._write_new_preflight_report(path, b"new")
    assert calls == []
    assert path.read_bytes() == b"existing"


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_symlinked_parent_is_denied_before_open(tmp_path: Path, monkeypatch) -> None:
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    try:
        linked.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation is not permitted")
    calls = []

    def forbidden_open(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("reparse-point parent must be denied before open")

    monkeypatch.setattr(cli.os, "open", forbidden_open)
    with pytest.raises(RuntimeError, match="non-reparse directory"):
        cli._write_new_preflight_report(linked / "preflight.json", b"new")
    assert calls == []
    assert not (real / "preflight.json").exists()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_final_symlink_is_denied_before_open(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "target.json"
    target.write_bytes(b"target")
    alias = tmp_path / "alias.json"
    try:
        alias.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("file symlink creation is not permitted")
    calls = []

    monkeypatch.setattr(
        cli.os,
        "open",
        lambda *args, **kwargs: calls.append(args) or (_ for _ in ()).throw(
            AssertionError("existing symlink must be denied before open")
        ),
    )
    with pytest.raises(RuntimeError, match="must be a new file"):
        cli._write_new_preflight_report(alias, b"new")
    assert calls == []
    assert target.read_bytes() == b"target"


def test_missing_parent_and_path_traversal_are_denied(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="path custody"):
        cli._write_new_preflight_report(tmp_path / "missing" / "report.json", b"x")
    traversing = tmp_path / "nested" / ".." / "report.json"
    with pytest.raises(RuntimeError, match="accepted local path"):
        cli._write_new_preflight_report(traversing, b"x")


@pytest.mark.parametrize("payload", (b"", b"x" * (cli._MAX_PREFLIGHT_REPORT_BYTES + 1), bytearray(b"x")))
def test_invalid_report_payload_is_denied_before_path_access(
    tmp_path: Path, monkeypatch, payload: object,
) -> None:
    calls = []

    def forbidden_lstat(self):
        calls.append(self)
        raise AssertionError("invalid payload must be rejected before path access")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(RuntimeError, match="payload is outside its byte budget"):
        cli._write_new_preflight_report(tmp_path / "report.json", payload)  # type: ignore[arg-type]
    assert calls == []
