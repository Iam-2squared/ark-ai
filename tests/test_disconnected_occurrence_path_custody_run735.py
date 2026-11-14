"""Local synthetic occurrence path custody; no authority or external dispatch."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)


def _link(source: Path, target: Path, *, directory: bool = False) -> None:
    try:
        target.symlink_to(source, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unsupported: {exc}")


def test_normal_occurrence_fixture_still_reopens(tmp_path: Path) -> None:
    store = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    assert store.count_synthetic() == 0
    reopened = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    assert reopened.count_synthetic() == 0


def test_valid_relative_occurrence_path_still_supported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    store = SyntheticOccurrenceStore(Path("occurrences.sqlite"))
    assert store.count_synthetic() == 0


def test_symbolic_ancestor_cannot_redirect_new_ledger(tmp_path: Path) -> None:
    real = tmp_path / "target"
    real.mkdir()
    link = tmp_path / "parent"
    _link(real, link, directory=True)
    with pytest.raises(SyntheticReplayRejected):
        SyntheticOccurrenceStore(link / "reserved.sqlite")
    assert not (real / "reserved.sqlite").exists()


def test_symbolic_leaf_cannot_be_used_as_existing_ledger(tmp_path: Path) -> None:
    original = tmp_path / "original.sqlite"
    SyntheticOccurrenceStore(original)
    link = tmp_path / "redirect.sqlite"
    _link(original, link)
    with pytest.raises(SyntheticReplayRejected):
        SyntheticOccurrenceStore(link)


def test_late_symbolic_leaf_refused_before_read_only_count(tmp_path: Path) -> None:
    path = tmp_path / "fixture.sqlite"
    store = SyntheticOccurrenceStore(path)
    new = tmp_path / "retained.sqlite"
    path.rename(new)
    _link(new, path)
    with pytest.raises(SyntheticReplayRejected):
        store.count_synthetic()


def test_late_hardlink_rejected_before_count(tmp_path: Path) -> None:
    path = tmp_path / "fixture.sqlite"
    store = SyntheticOccurrenceStore(path)
    try:
        os.link(path, tmp_path / "alias.sqlite")
    except OSError as exc:
        pytest.skip(f"hardlinks unsupported: {exc}")
    with pytest.raises(SyntheticReplayRejected):
        store.count_synthetic()


def test_missing_store_refused_without_recreation(tmp_path: Path) -> None:
    path = tmp_path / "fixture.sqlite"
    store = SyntheticOccurrenceStore(path)
    path.rename(tmp_path / "held.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        store.count_synthetic()
    assert not path.exists()


def test_parent_traversal_rejected_before_bootstrap(tmp_path: Path) -> None:
    with pytest.raises(SyntheticReplayRejected):
        SyntheticOccurrenceStore(tmp_path / "x" / ".." / "escape.sqlite")
    assert not (tmp_path / "escape.sqlite").exists()


@pytest.mark.parametrize("case", ["directory", "file-as-parent"])
def test_nonregular_occurrence_paths_refused(tmp_path: Path, case: str) -> None:
    if case == "directory":
        path = tmp_path / "database-is-directory"
        path.mkdir()
    else:
        p = tmp_path / "parent-file"
        p.write_text("inert", encoding="utf-8")
        path = p / "fixture.sqlite"
    with pytest.raises(SyntheticReplayRejected):
        SyntheticOccurrenceStore(path)


def test_custom_pathlike_not_evaluated() -> None:
    calls: list[str] = []

    class HostilePath:
        def __fspath__(self) -> str:
            calls.append("private path requested")
            return "private.sqlite"

    with pytest.raises(TypeError):
        SyntheticOccurrenceStore(HostilePath())  # type: ignore[arg-type]
    assert calls == []
