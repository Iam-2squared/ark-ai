"""ActionAudit path admission pins stat policy across metadata callbacks.

Synthetic in-process substitutions and temporary files only. No private audit
database, authenticated evidence, or external action is opened or performed.
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

import ark.agency.audit as audit_module
from ark.agency.contracts import ActionAuditSchemaError


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG", "S_IFMT"))
def test_stat_predicate_rebinding_from_lstat_callback_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(audit_module.stat, name, lambda *_args: True)
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
            patch.setattr(audit_module.stat, "S_ISREG", lambda *_args: True)
            raise FileNotFoundError
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(target, allow_new_parents=True)


def test_stat_policy_rebinding_from_mode_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReentrantMetadata:
        @property
        def st_mode(self) -> int:
            patch.setattr(audit_module.stat, "S_ISDIR", lambda *_args: True)
            return stat.S_IFDIR | 0o700

        st_file_attributes = 0

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    original_lstat = Path.lstat
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
    class ReentrantMetadata:
        st_mode = stat.S_IFDIR | 0o700

        @property
        def st_file_attributes(self) -> int:
            patch.setattr(audit_module.stat, "S_ISLNK", lambda *_args: True)
            return 0

    original_lstat = Path.lstat

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


def test_stat_policy_rebinding_from_main_link_count_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "audit.sqlite"
    target.write_bytes(b"synthetic main file")

    class ReentrantMetadata:
        st_mode = stat.S_IFREG | 0o600
        st_file_attributes = 0

        @property
        def st_nlink(self) -> int:
            patch.setattr(audit_module.stat, "S_ISREG", lambda *_args: False)
            return 1

    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == target:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(target, allow_new_parents=True)


def test_stat_policy_rebinding_from_sidecar_link_count_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "audit.sqlite"
    sidecar = target.with_name(target.name + "-wal")
    target.write_bytes(b"synthetic main file")
    sidecar.write_bytes(b"synthetic sidecar")

    class ReentrantMetadata:
        st_mode = stat.S_IFREG | 0o600
        st_file_attributes = 0

        @property
        def st_nlink(self) -> int:
            patch.setattr(audit_module.stat, "S_ISREG", lambda *_args: False)
            return 1

    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == sidecar:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(target, allow_new_parents=True)


def test_stat_policy_rebinding_from_sidecar_recheck_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "audit.sqlite"
    sidecar = target.with_name(target.name + "-wal")
    target.write_bytes(b"synthetic main file")
    sidecar.write_bytes(b"synthetic sidecar")
    original_lstat = Path.lstat
    calls = 0

    class Metadata:
        st_mode = stat.S_IFREG | 0o600
        st_file_attributes = 0

        def __init__(self, links: int) -> None:
            self.st_nlink = links

    def reentrant_lstat(path: Path):
        nonlocal calls
        if path == sidecar:
            calls += 1
            if calls == 2:
                patch.setattr(audit_module.stat, "S_ISREG", lambda *_args: False)
            return Metadata(0 if calls == 1 else 1)
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            ActionAuditSchemaError, match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(target, allow_new_parents=True)
        assert calls == 2
