"""Single-sweep post-stat ancestry custody for disposable POSIX SQLite fixtures.

Held file descriptors can outlive a rename of their named parent. A clean FD
recheck alone does not prove the named ancestry still selects those handles.
This is a local inspection regression, NOT future path custody or WAL proof.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from ark import disconnected_sqlite_sidecar_custody as custody

pytestmark = pytest.mark.skipif(
    os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0),
    reason="requires POSIX no-follow descriptor-relative inspection",
)


def _fixture(tmp_path: Path) -> Path:
    parent = tmp_path / "held-parent"
    parent.mkdir()
    path = parent / "fixture.sqlite"
    path.write_bytes(b"disconnected metadata only")
    return path


def _retarget(path: Path) -> Path:
    parent = path.parent
    moved = parent.with_name("renamed-parent")
    parent.rename(moved)
    parent.symlink_to(moved, target_is_directory=True)
    return moved


def _restore(path: Path, moved: Path) -> None:
    path.parent.unlink()
    moved.rename(path.parent)


@pytest.mark.parametrize(
    "trigger", ("fixture.sqlite", "fixture.sqlite-wal", "fixture.sqlite-journal")
)
def test_final_named_file_stat_retarget_requires_new_ancestry_scan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, trigger: str,
) -> None:
    path = _fixture(tmp_path)
    original_stat = custody.os.stat
    moved = []
    calls = []

    def swap_on_last_named_file(name, *args, **kwargs):
        if name == trigger and kwargs.get("dir_fd") is not None and not moved:
            moved.append(_retarget(path))
            calls.append(name)
        return original_stat(name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(custody.os, "stat", swap_on_last_named_file)
        with pytest.raises(custody.SQLiteSidecarCustodyRejected):
            custody._capture_once(path)
    assert calls == [trigger]
    _restore(path, moved[0])
    seal = custody.capture_disconnected_sqlite_sidecars(path)
    assert seal.tool_execution_authorized is False
    assert seal.stable_future_path_proven is False


def test_retarget_during_held_fd_metadata_recheck_is_not_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _fixture(tmp_path)
    original_file_id = custody._file_id
    calls = []
    moved = []

    def swap_at_final_fd_recheck(stat_result):
        calls.append(True)
        # With no sidecars: open FD, named stat, then final held FD recheck.
        if len(calls) == 3:
            moved.append(_retarget(path))
        return original_file_id(stat_result)

    with monkeypatch.context() as patch:
        patch.setattr(custody, "_file_id", swap_at_final_fd_recheck)
        with pytest.raises(custody.SQLiteSidecarCustodyRejected):
            custody._capture_once(path)
    assert len(calls) >= 3
    assert len(moved) == 1
    _restore(path, moved[0])
    assert custody.capture_disconnected_sqlite_sidecars(path).consent_verified is False
