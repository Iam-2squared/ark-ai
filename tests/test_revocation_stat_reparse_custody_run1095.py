"""Run1095: revocation path classification pins stat predicates and Windows reparse bits.

All filesystem objects are disposable synthetic fixtures. These checks are
not atomic handle custody, authenticated consent, or secure erasure.
"""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.personal_context_revocation_review import (
    SyntheticContextRevocationRejected,
    _check_local_revocation_path,
)


def test_stat_predicate_replacement_is_rejected_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched: list[Path] = []

    def forbidden_lstat(path: Path):
        touched.append(path)
        raise AssertionError("filesystem access must not run before stat policy admission")

    with monkeypatch.context() as patch:
        patch.setattr(stat, "S_ISDIR", lambda _mode: True)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            SyntheticContextRevocationRejected, match="stat policy changed",
        ):
            _check_local_revocation_path(tmp_path / "veto.sqlite")

    assert touched == []


def test_stat_predicate_replacement_during_lstat_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat
    touched: list[Path] = []

    def mutate_after_lstat(path: Path):
        result = original_lstat(path)
        touched.append(path)
        stat.S_ISDIR = lambda _mode: True
        return result

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", mutate_after_lstat)
        with pytest.raises(
            SyntheticContextRevocationRejected, match="stat policy changed",
        ):
            _check_local_revocation_path(tmp_path / "veto.sqlite")

    assert len(touched) == 1


def test_reparse_mask_replacement_is_rejected_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched: list[Path] = []

    def forbidden_lstat(path: Path):
        touched.append(path)
        raise AssertionError("reparse policy must be checked before lstat")

    with monkeypatch.context() as patch:
        patch.setattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x800, raising=False)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            SyntheticContextRevocationRejected, match="stat policy changed",
        ):
            _check_local_revocation_path(tmp_path / "veto.sqlite")

    assert touched == []


def test_windows_reparse_ancestor_is_not_admitted_as_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "veto.sqlite"
    original_lstat = Path.lstat
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

    def mark_parent(pathname: Path):
        if pathname == tmp_path:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR | 0o755,
                st_nlink=1,
                st_file_attributes=reparse,
            )
        return original_lstat(pathname)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", mark_parent)
        with pytest.raises(
            SyntheticContextRevocationRejected, match="ancestor",
        ):
            _check_local_revocation_path(path)


def test_windows_reparse_source_is_not_admitted_as_regular_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "veto.sqlite"
    path.write_bytes(b"synthetic")
    original_lstat = Path.lstat
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

    def mark_source(pathname: Path):
        if pathname == path:
            return SimpleNamespace(
                st_mode=stat.S_IFREG | 0o600,
                st_nlink=1,
                st_file_attributes=reparse,
            )
        return original_lstat(pathname)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", mark_source)
        with pytest.raises(
            SyntheticContextRevocationRejected, match="regular-file link",
        ):
            _check_local_revocation_path(path)


def test_windows_reparse_sqlite_sidecar_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "veto.sqlite"
    sidecar = path.with_name(path.name + "-wal")
    path.write_bytes(b"synthetic")
    sidecar.write_bytes(b"synthetic-wal")
    original_lstat = Path.lstat
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

    def mark_sidecar(pathname: Path):
        if pathname == sidecar:
            return SimpleNamespace(
                st_mode=stat.S_IFREG | 0o600,
                st_nlink=1,
                st_file_attributes=reparse,
            )
        return original_lstat(pathname)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", mark_sidecar)
        with pytest.raises(
            SyntheticContextRevocationRejected, match="unsafe revocation SQLite sidecar",
        ):
            _check_local_revocation_path(path)
