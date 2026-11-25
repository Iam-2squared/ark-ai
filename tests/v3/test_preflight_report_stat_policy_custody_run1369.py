"""Run1369: V3 evidence paths pin stat policy across metadata callbacks.

Only temporary paths and synthetic metadata are used. No torch, GPU, model,
preflight backend, training, or Candidate operation is invoked.
"""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import training_cli as cli


def _forbidden_lstat(_path: Path):
    raise AssertionError("filesystem inspected after evidence stat-policy substitution")


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG"))
def test_stat_predicate_rebinding_is_denied_before_report_path_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(cli.stat, name, lambda *_args: True)
        patch.setattr(Path, "lstat", _forbidden_lstat)
        with pytest.raises(RuntimeError, match="evidence path policy changed"):
            cli._write_new_preflight_report(tmp_path / "report.json", b"{}")


def test_stat_module_rebinding_is_denied_before_report_path_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(cli, "stat", object())
        patch.setattr(Path, "lstat", _forbidden_lstat)
        with pytest.raises(RuntimeError, match="evidence path policy changed"):
            cli._write_new_preflight_report(tmp_path / "report.json", b"{}")


def test_reparse_mask_rebinding_is_denied_before_report_path_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(cli, "_REPARSE_POINT_ATTRIBUTE", 0x800)
        patch.setattr(Path, "lstat", _forbidden_lstat)
        with pytest.raises(RuntimeError, match="evidence path policy changed"):
            cli._write_new_preflight_report(tmp_path / "report.json", b"{}")


def test_path_policy_guard_rebinding_is_detected_by_original_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = cli._ORIGINAL_EVIDENCE_PATH_POLICY_GUARD
    with monkeypatch.context() as patch:
        patch.setattr(cli, "_require_original_evidence_path_policy", lambda: None)
        with pytest.raises(RuntimeError, match="evidence path policy changed"):
            original()


def test_stat_predicate_rebinding_from_parent_lstat_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        info = original_lstat(path)
        if path == tmp_path:
            patch.setattr(cli.stat, "S_ISDIR", lambda *_args: True)
        return info

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(RuntimeError, match="evidence path policy changed"):
            cli._write_new_preflight_report(tmp_path / "report.json", b"{}")


def test_reparse_metadata_accessor_rebinding_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReentrantMetadata:
        st_mode = stat.S_IFDIR | 0o700

        @property
        def st_file_attributes(self) -> int:
            patch.setattr(cli.stat, "S_ISLNK", lambda *_args: True)
            return 0

    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(RuntimeError, match="evidence path policy changed"):
            cli._write_new_preflight_report(tmp_path / "report.json", b"{}")


def test_windows_reparse_parent_is_denied_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened: list[Path] = []

    def marked_lstat(path: Path):
        if path == tmp_path:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR | 0o700,
                st_file_attributes=0x400,
            )
        return Path.lstat(path)

    def forbidden_open(path: Path, *_args, **_kwargs) -> int:
        opened.append(path)
        raise AssertionError("Windows reparse parent must be denied before open")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", marked_lstat)
        patch.setattr(cli.os, "open", forbidden_open)
        with pytest.raises(RuntimeError, match="non-reparse directory"):
            cli._write_new_preflight_report(tmp_path / "report.json", b"{}")
    assert opened == []
