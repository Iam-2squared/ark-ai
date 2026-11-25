"""Run1359: ActionAudit rechecks pinned stat policy after metadata callbacks."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

import ark.agency.audit as audit_module
from ark.agency.contracts import ActionAuditSchemaError


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG", "S_IFMT"))
def test_stat_predicate_replacement_from_lstat_is_denied_before_classification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(audit_module.stat, name, lambda *_args: True)
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError,
            match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite3",
                allow_new_parents=True,
            )


def test_stat_module_replacement_from_lstat_is_denied_before_classification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(audit_module, "stat", object())
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError,
            match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite3",
                allow_new_parents=True,
            )


@pytest.mark.parametrize("field", ("st_mode", "st_file_attributes"))
def test_reentrant_metadata_accessor_cannot_replace_stat_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    class ReentrantMetadata:
        st_nlink = 1

        @property
        def st_mode(self) -> int:
            if field == "st_mode":
                patch.setattr(
                    audit_module.stat,
                    "S_ISDIR",
                    lambda *_args: True,
                )
            return stat.S_IFDIR | 0o700

        @property
        def st_file_attributes(self) -> int:
            if field == "st_file_attributes":
                patch.setattr(
                    audit_module.stat,
                    "S_ISLNK",
                    lambda *_args: False,
                )
            return 0

    original_lstat = Path.lstat

    def synthetic_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", synthetic_lstat)
        with pytest.raises(
            ActionAuditSchemaError,
            match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite3",
                allow_new_parents=True,
            )


def test_missing_database_callback_cannot_replace_stat_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "audit.sqlite3"
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == target:
            patch.setattr(
                audit_module.stat,
                "S_ISREG",
                lambda *_args: True,
            )
            raise FileNotFoundError
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError,
            match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                target,
                allow_new_parents=True,
            )

    assert not target.exists()


def test_missing_sidecar_callback_cannot_replace_stat_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "audit.sqlite3"
    target.write_bytes(b"synthetic action audit marker")
    sidecar = target.with_name(target.name + "-wal")
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == sidecar:
            patch.setattr(
                audit_module.stat,
                "S_ISREG",
                lambda *_args: True,
            )
            raise FileNotFoundError
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError,
            match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                target,
                allow_new_parents=False,
            )

    assert target.read_bytes() == b"synthetic action audit marker"


def test_original_stat_policy_keeps_valid_audit_path_admissible(
    tmp_path: Path,
) -> None:
    target = tmp_path / "audit.sqlite3"
    target.write_bytes(b"synthetic action audit marker")

    audit_module._require_safe_audit_path(
        target,
        allow_new_parents=False,
    )
