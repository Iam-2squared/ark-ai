"""Synthetic cross-store audit-link path preflight; no real authority."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkRejected,
    SyntheticOccurrenceAuditLinkStore,
)


def _link(source: Path, target: Path, *, directory: bool = False) -> None:
    try:
        target.symlink_to(source, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unsupported: {exc}")


def test_empty_link_ledger_reads_and_restarts(tmp_path: Path) -> None:
    path = tmp_path / "links.sqlite"
    store = SyntheticOccurrenceAuditLinkStore(path)
    assert store.read_witness().event_count == 0
    assert SyntheticOccurrenceAuditLinkStore(path).read_witness().event_count == 0


def test_relative_link_path_keeps_local_fixture_compatibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert SyntheticOccurrenceAuditLinkStore(
        Path("links.sqlite")
    ).read_witness().event_count == 0


def test_symbolic_parent_denied_before_link_db_created(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    _link(real, alias, directory=True)
    with pytest.raises(SyntheticAuditLinkRejected):
        SyntheticOccurrenceAuditLinkStore(alias / "links.sqlite")
    assert not (real / "links.sqlite").exists()


def test_symbolic_leaf_denied_on_new_object(tmp_path: Path) -> None:
    real = tmp_path / "links.sqlite"
    SyntheticOccurrenceAuditLinkStore(real)
    alias = tmp_path / "alias.sqlite"
    _link(real, alias)
    with pytest.raises(SyntheticAuditLinkRejected):
        SyntheticOccurrenceAuditLinkStore(alias)


def test_late_leaf_symlink_denied_before_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "links.sqlite"
    store = SyntheticOccurrenceAuditLinkStore(path)
    real = tmp_path / "original.sqlite"
    path.rename(real)
    _link(real, path)
    with pytest.raises(SyntheticAuditLinkRejected):
        store.read_witness()


def test_late_hardlink_denied_before_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "links.sqlite"
    store = SyntheticOccurrenceAuditLinkStore(path)
    try:
        os.link(path, tmp_path / "extra-link.sqlite")
    except OSError as exc:
        pytest.skip(f"hardlinks unsupported: {exc}")
    with pytest.raises(SyntheticAuditLinkRejected):
        store.read_witness()


def test_missing_link_database_after_startup_is_not_recreated(tmp_path: Path) -> None:
    path = tmp_path / "links.sqlite"
    store = SyntheticOccurrenceAuditLinkStore(path)
    path.rename(tmp_path / "held.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        store.read_witness()
    assert not path.exists()


def test_parent_traversal_refused_before_open(tmp_path: Path) -> None:
    with pytest.raises(SyntheticAuditLinkRejected):
        SyntheticOccurrenceAuditLinkStore(tmp_path / "x" / ".." / "links.sqlite")
    assert not (tmp_path / "links.sqlite").exists()


@pytest.mark.parametrize("kind", ["directory", "nondirectory-parent"])
def test_unusable_link_target_refused(tmp_path: Path, kind: str) -> None:
    if kind == "directory":
        path = tmp_path / "path-is-dir"
        path.mkdir()
    else:
        parent = tmp_path / "parent-file"
        parent.write_text("fixture", encoding="utf-8")
        path = parent / "links.sqlite"
    with pytest.raises(SyntheticAuditLinkRejected):
        SyntheticOccurrenceAuditLinkStore(path)


def test_hostile_pathlike_not_invoked() -> None:
    touched: list[str] = []

    class Hostile:
        def __fspath__(self) -> str:
            touched.append("called")
            return "secret.db"

    with pytest.raises(TypeError):
        SyntheticOccurrenceAuditLinkStore(Hostile())  # type: ignore[arg-type]
    assert not touched
