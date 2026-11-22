"""Run1116: reject symlink entries before descending a local V3 code tree."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.learning.identity as identity


def _fake_project(tmp_path: Path) -> Path:
    learning = tmp_path / "src" / "ark" / "learning"
    learning.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'ark-fixture'\n", encoding="utf-8",
    )
    (learning / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    return learning


def _symlink_or_skip(link: Path, target: Path, *, directory: bool) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"filesystem symlinks are unavailable: {exc}")


def test_symlink_directory_is_rejected_before_target_scandir(
    tmp_path, monkeypatch,
):
    learning = _fake_project(tmp_path)
    outside = tmp_path / "outside-learning-root"
    outside.mkdir()
    (outside / "must-not-be-enumerated.py").write_text(
        "PRIVATE_FIXTURE = True\n", encoding="utf-8",
    )
    _symlink_or_skip(learning / "external", outside, directory=True)

    scanned_targets = []
    original_scandir = identity.os.scandir

    def record_scandir(path):
        if Path(path) == outside:
            scanned_targets.append(Path(path))
        return original_scandir(path)

    monkeypatch.setattr(identity.os, "scandir", record_scandir)
    with pytest.raises(ValueError, match="symlink entry"):
        identity.build_code_tree_identity(tmp_path)

    assert scanned_targets == []


def test_symlinked_python_file_is_rejected(tmp_path):
    learning = _fake_project(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("PRIVATE_FIXTURE = True\n", encoding="utf-8")
    _symlink_or_skip(learning / "linked.py", outside, directory=False)

    with pytest.raises(ValueError, match="symlink entry"):
        identity.build_code_tree_identity(tmp_path)


def test_windows_snapshot_epoch_uses_path_identity_not_direntry_file_id(
    tmp_path, monkeypatch,
):
    learning = _fake_project(tmp_path)

    def forbidden_samestat(*_args):
        raise AssertionError(
            "Windows snapshot enumeration must not compare DirEntry and Path file IDs"
        )

    monkeypatch.setattr(
        identity,
        "os",
        SimpleNamespace(
            name="nt",
            scandir=os.scandir,
            path=SimpleNamespace(samestat=forbidden_samestat),
        ),
    )
    entries = identity._snapshot_entries(learning)

    assert [(relative, is_dir) for relative, _, is_dir, _ in entries] == [
        ("", True),
        ("core.py", False),
    ]
