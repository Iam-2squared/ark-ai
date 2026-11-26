"""Bound one SQLite-veto sidecar re-observation at last close.

Disposable filesystem metadata only; no consent, live Memory, identity
attestation or disclosure is established by these tests.
"""

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
    _path,
)


def _one_unlinked_lstat(monkeypatch: pytest.MonkeyPatch, sidecar: Path) -> list[int]:
    path_type = type(sidecar)
    original = path_type.lstat
    observed: list[int] = []

    def replacement(self: Path, *args: object, **kwargs: object) -> object:
        if self == sidecar:
            observed.append(1)
            if len(observed) == 1:
                return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(path_type, "lstat", replacement)
    return observed


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_disappearing_regular_sidecar_is_reobserved_at_most_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, suffix: str,
) -> None:
    db = tmp_path / "veto.sqlite"
    DisconnectedPrivacyVetoLedger(db)
    sidecar = db.with_name(db.name + suffix)
    assert not sidecar.exists()
    observed = _one_unlinked_lstat(monkeypatch, sidecar)
    assert _path(db, exists=True) == db
    assert observed == [1, 1]


@pytest.mark.parametrize("kind", ("regular", "hardlink", "symlink"))
def test_reobservation_accepts_only_a_fresh_single_link_regular_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    db = tmp_path / "veto.sqlite"
    DisconnectedPrivacyVetoLedger(db)
    sidecar = db.with_name(db.name + "-journal")
    other = tmp_path / "untouched"
    other.write_bytes(b"unrelated fixture")
    if kind == "regular":
        sidecar.write_bytes(b"synthetic regular sidecar")
    else:
        try:
            if kind == "hardlink":
                sidecar.hardlink_to(other)
            else:
                sidecar.symlink_to(other)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"filesystem does not support {kind}: {exc}")
    observed = _one_unlinked_lstat(monkeypatch, sidecar)
    if kind == "regular":
        assert _path(db, exists=True) == db
    else:
        with pytest.raises(OfflinePrivacyVetoRejected, match="sidecar alias"):
            _path(db, exists=True)
    assert observed == [1, 1]
    assert other.read_bytes() == b"unrelated fixture"


def test_permanently_unlinked_regular_inode_remains_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "veto.sqlite"
    DisconnectedPrivacyVetoLedger(db)
    sidecar = db.with_name(db.name + "-journal")
    original = type(sidecar).lstat
    observed: list[int] = []

    def unlinked(self: Path, *args: object, **kwargs: object) -> object:
        if self == sidecar:
            observed.append(1)
            return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(sidecar), "lstat", unlinked)
    with pytest.raises(OfflinePrivacyVetoRejected, match="sidecar alias"):
        _path(db, exists=True)
    assert observed == [1, 1]


def test_orphaned_unlinked_sidecar_is_rejected_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "missing.sqlite"
    sidecar = db.with_name(db.name + "-journal")
    observed = _one_unlinked_lstat(monkeypatch, sidecar)
    with pytest.raises(OfflinePrivacyVetoRejected, match="orphaned"):
        _path(db, exists=False)
    assert observed == [1]
    assert not db.exists()
