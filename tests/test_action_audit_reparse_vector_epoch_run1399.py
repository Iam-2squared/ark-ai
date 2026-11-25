"""Run1399: ActionAudit reparse policy retains its complete stat epoch."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.agency.audit as audit_module
from ark.agency.contracts import ActionAuditSchemaError


def _install_joint_stat_replacement(
    patch: pytest.MonkeyPatch,
    calls: list[str],
) -> None:
    def hostile(name: str):
        def reject(*_args: object, **_kwargs: object) -> bool:
            calls.append(name)
            raise AssertionError("substituted ActionAudit stat predicate executed")

        return reject

    is_dir = hostile("S_ISDIR")
    is_link = hostile("S_ISLNK")
    is_regular = hostile("S_ISREG")
    file_type = hostile("S_IFMT")
    fake_stat = SimpleNamespace(
        S_ISDIR=is_dir,
        S_ISLNK=is_link,
        S_ISREG=is_regular,
        S_IFMT=file_type,
    )
    forged_epoch = (
        fake_stat,
        is_dir,
        is_link,
        is_regular,
        file_type,
        0,
    )
    patch.setattr(audit_module, "stat", fake_stat)
    patch.setattr(audit_module, "_ORIGINAL_STAT", fake_stat)
    patch.setattr(audit_module, "_ORIGINAL_STAT_S_ISDIR", is_dir)
    patch.setattr(audit_module, "_ORIGINAL_STAT_S_ISLNK", is_link)
    patch.setattr(audit_module, "_ORIGINAL_STAT_S_ISREG", is_regular)
    patch.setattr(audit_module, "_ORIGINAL_STAT_IFMT", file_type)
    patch.setattr(audit_module, "_REPARSE_POINT_ATTRIBUTE", 0)
    patch.setattr(audit_module, "_ORIGINAL_REPARSE_POINT_ATTRIBUTE", 0)
    patch.setattr(audit_module, "_ORIGINAL_AUDIT_REPARSE_POLICY_EPOCH", forged_epoch)


def test_joint_stat_module_predicate_and_epoch_replacement_is_denied_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    with monkeypatch.context() as patch:
        _install_joint_stat_replacement(patch, calls)

        def forbidden_lstat(_path: Path):
            raise AssertionError("filesystem inspected before ActionAudit denial")

        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            ActionAuditSchemaError,
            match="audit reparse-point policy changed",
        ):
            audit_module._require_safe_audit_path(
                tmp_path / "audit.sqlite",
                allow_new_parents=True,
            )

    assert calls == []


def test_reentrant_metadata_replacement_is_denied_before_mode_or_predicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    mode_reads: list[str] = []

    class ReentrantMetadata:
        @property
        def st_file_attributes(self) -> int:
            _install_joint_stat_replacement(patch, calls)
            return 0

        @property
        def st_mode(self) -> int:
            mode_reads.append("st_mode")
            return 0

    with monkeypatch.context() as patch:
        with pytest.raises(
            ActionAuditSchemaError,
            match="audit reparse-point policy changed",
        ):
            audit_module._is_reparse_point(ReentrantMetadata())

    assert calls == []
    assert mode_reads == []
