"""Planner journal last-close SQLite pathname race, with no real dispatch.

Only a disposable path stub is inspected; the tests never open it as SQLite.
A transient already-unlinked regular inode may disappear; aliases and orphan
sidecars must still be denied without returning execution authority.
"""

from __future__ import annotations

import stat
from types import SimpleNamespace

import pytest

from ark.agency.planner_journal_review import (
    SyntheticPlanJournalRejected,
    _require_safe_journal_path,
)


def _fake_first_unlinked(monkeypatch, sidecar, *, mode=stat.S_IFREG):
    kind = type(sidecar)
    original = kind.lstat
    seen = []

    def inspect(self, *args, **kwargs):
        if self == sidecar:
            seen.append(1)
            if len(seen) == 1:
                return SimpleNamespace(st_mode=mode | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(kind, "lstat", inspect)
    return seen


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_transient_unlinked_regular_inode_is_reobserved_once(
    tmp_path, monkeypatch, suffix,
):
    db = tmp_path / "planner-journal.sqlite"
    db.write_bytes(b"disposable path-only stub")
    sidecar = db.with_name(db.name + suffix)
    observed = _fake_first_unlinked(monkeypatch, sidecar)
    _require_safe_journal_path(db)
    assert observed == [1, 1]
    assert not sidecar.exists()


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
@pytest.mark.parametrize("replacement", ("regular", "hardlink", "symlink"))
def test_stale_unlinked_inode_never_launders_replacement_alias(
    tmp_path, monkeypatch, suffix, replacement,
):
    db = tmp_path / "planner-journal.sqlite"
    db.write_bytes(b"no SQLite connection")
    sidecar = db.with_name(db.name + suffix)
    if replacement == "regular":
        sidecar.write_bytes(b"new harmless single-link inode")
    else:
        target = tmp_path / "unrelated-fixture"
        target.write_bytes(b"must remain intact")
        try:
            if replacement == "hardlink":
                sidecar.hardlink_to(target)
            else:
                sidecar.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"filesystem cannot create {replacement}: {exc}")
    observed = _fake_first_unlinked(monkeypatch, sidecar)
    if replacement == "regular":
        _require_safe_journal_path(db)
    else:
        with pytest.raises(SyntheticPlanJournalRejected, match="sidecar"):
            _require_safe_journal_path(db)
        assert target.read_bytes() == b"must remain intact"
    assert observed == [1, 1]


def test_permanently_unlinked_inode_is_denied_after_one_recheck(
    tmp_path, monkeypatch,
):
    db = tmp_path / "planner-journal.sqlite"
    db.write_bytes(b"disposable")
    sidecar = db.with_name(db.name + "-journal")
    kind = type(sidecar)
    original = kind.lstat
    observed = []

    def unlinking(self, *args, **kwargs):
        if self == sidecar:
            observed.append(1)
            return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(kind, "lstat", unlinking)
    with pytest.raises(SyntheticPlanJournalRejected, match="sidecar"):
        _require_safe_journal_path(db)
    assert observed == [1, 1]


@pytest.mark.parametrize("mode", (stat.S_IFLNK, stat.S_IFDIR))
def test_nonregular_zero_link_snapshot_is_never_retried(
    tmp_path, monkeypatch, mode,
):
    db = tmp_path / "planner-journal.sqlite"
    db.write_bytes(b"disposable")
    sidecar = db.with_name(db.name + "-wal")
    observed = _fake_first_unlinked(monkeypatch, sidecar, mode=mode)
    with pytest.raises(SyntheticPlanJournalRejected, match="sidecar"):
        _require_safe_journal_path(db)
    assert observed == [1]


def test_orphan_unsafe_sidecar_never_gets_retry_or_creates_main(
    tmp_path, monkeypatch,
):
    db = tmp_path / "absent.sqlite"
    sidecar = db.with_name(db.name + "-shm")
    observed = _fake_first_unlinked(monkeypatch, sidecar)
    with pytest.raises(SyntheticPlanJournalRejected, match="orphaned"):
        _require_safe_journal_path(db)
    assert observed == [1]
    assert not db.exists()
