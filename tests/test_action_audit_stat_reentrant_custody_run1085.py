"""ActionAudit path admission pins stat policy across metadata callbacks.

Synthetic in-process substitutions only; no audit database or external action
is opened or performed.
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

import ark.agency.audit as audit_module
from ark.agency.contracts import ActionAuditSchemaError


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG", "S_IFMT"))
def test_stat_predicate_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat predicate substitution")

    with monkeypatch.context() as patch:
        patch.setattr(audit_module.stat, name, lambda *_args: True)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite", allow_new_parents=True,
            )


def test_stat_module_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat module substitution")

    with monkeypatch.context() as patch:
        patch.setattr(audit_module, "stat", object())
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite", allow_new_parents=True,
            )


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG", "S_IFMT"))
def test_stat_predicate_rebinding_from_lstat_callback_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        setattr(audit_module.stat, name, lambda *_args: True)
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite", allow_new_parents=True,
            )


def test_stat_module_rebinding_from_lstat_callback_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(audit_module, "stat", object())
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite", allow_new_parents=True,
            )


def test_stat_policy_rebinding_on_missing_leaf_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat
    target = tmp_path / "audit.sqlite"

    def reentrant_lstat(path: Path):
        if path == target:
            audit_module.stat.S_ISREG = lambda *_args: True
            raise FileNotFoundError
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                target, allow_new_parents=True,
            )


def test_stat_policy_rebinding_from_mode_metadata_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    class ReentrantMetadata:
        @property
        def st_mode(self) -> int:
            audit_module.stat.S_ISDIR = lambda *_args: True
            return stat.S_IFDIR | 0o700

        st_file_attributes = 0

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite", allow_new_parents=True,
            )


def test_stat_policy_rebinding_from_windows_attribute_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    class ReentrantMetadata:
        st_mode = stat.S_IFDIR | 0o700

        @property
        def st_file_attributes(self) -> int:
            audit_module.stat.S_ISLNK = lambda *_args: True
            return 0

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite", allow_new_parents=True,
            )
