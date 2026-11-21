"""Windows reparse-point admission tests for the disconnected Planner journal.

Synthetic stat metadata only; no privileged junction, SQLite dispatch or replay.
"""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.agency.planner_journal_review as journal


def _reparse_info(mode: int):
    return SimpleNamespace(
        st_mode=mode,
        st_file_attributes=0x400,
        st_nlink=1,
    )


def test_reparse_point_ancestor_is_rejected_before_journal_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "junction"
    parent.mkdir()
    path = parent / "plan.sqlite"
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == parent:
            return _reparse_info(stat.S_IFDIR | 0o755)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        journal.SyntheticPlanJournalRejected,
        match="reparse-point ancestor",
    ):
        journal._require_safe_journal_path(path)

    assert not path.exists()


def test_reparse_point_database_leaf_is_rejected_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "plan.sqlite"
    path.write_bytes(b"synthetic database marker")
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == path:
            return _reparse_info(stat.S_IFREG | 0o600)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        journal.SyntheticPlanJournalRejected,
        match="reparse-point path",
    ):
        journal._require_safe_journal_path(path)

    assert path.read_bytes() == b"synthetic database marker"


def test_reparse_point_sqlite_sidecar_is_rejected_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "plan.sqlite"
    path.write_bytes(b"synthetic database marker")
    sidecar = path.with_name(path.name + "-wal")
    sidecar.write_bytes(b"synthetic sidecar marker")
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == sidecar:
            return _reparse_info(stat.S_IFREG | 0o600)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        journal.SyntheticPlanJournalRejected,
        match="sidecar reparse-point",
    ):
        journal._require_safe_journal_path(path)

    assert path.exists()
    assert sidecar.read_bytes() == b"synthetic sidecar marker"


def test_reparse_point_policy_rebinding_is_rejected_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(journal, "_REPARSE_POINT_ATTRIBUTE", 0x800)

    def forbidden_lstat(_candidate: Path):
        raise AssertionError("reparse policy must be checked before lstat")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(
        journal.SyntheticPlanJournalRejected,
        match="reparse-point policy changed",
    ):
        journal._require_safe_journal_path(tmp_path / "plan.sqlite")


@pytest.mark.parametrize("attributes", (True, None, "1024", 1024.0))
def test_malformed_reparse_metadata_fails_closed(attributes) -> None:
    metadata = SimpleNamespace(st_file_attributes=attributes)
    with pytest.raises(
        journal.SyntheticPlanJournalRejected,
        match="reparse metadata is malformed",
    ):
        journal._has_windows_reparse_point(metadata)


def test_absent_platform_attribute_uses_non_reparse_default() -> None:
    assert journal._has_windows_reparse_point(SimpleNamespace()) is False


def test_malformed_ancestor_metadata_is_rejected_before_leaf_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    path = parent / "plan.sqlite"
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == parent:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR | 0o755,
                st_file_attributes=True,
            )
        if candidate == path:
            raise AssertionError("leaf inspected after malformed ancestor metadata")
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        journal.SyntheticPlanJournalRejected,
        match="reparse metadata is malformed",
    ):
        journal._require_safe_journal_path(path)
