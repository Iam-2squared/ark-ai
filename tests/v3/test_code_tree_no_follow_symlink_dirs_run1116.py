"""Run1116: reject symlink entries before descending a local V3 code tree."""

from __future__ import annotations

from pathlib import Path

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


def test_windows_direntry_metadata_comparison_ignores_file_ids_and_ctime():
    entry_epoch = (1, 2, 0o100644, 12, 34, 56, 1)
    path_epoch = (9, 8, 0o100644, 12, 34, 99, 1)

    assert identity._entry_metadata_matches_path(
        entry_epoch, path_epoch, windows=True, is_dir=False,
    )
    assert not identity._entry_metadata_matches_path(
        entry_epoch, path_epoch, windows=False, is_dir=False,
    )

    changed_size = (9, 8, 0o100644, 13, 34, 99, 1)
    changed_mtime = (9, 8, 0o100644, 12, 35, 99, 1)
    changed_mode = (9, 8, 0o100600, 12, 34, 99, 1)
    changed_links = (9, 8, 0o100644, 12, 34, 99, 2)
    assert identity._entry_metadata_matches_path(
        entry_epoch, changed_links, windows=True, is_dir=False,
    )
    for changed in (changed_size, changed_mtime, changed_mode):
        assert not identity._entry_metadata_matches_path(
            entry_epoch, changed, windows=True, is_dir=False,
        )
