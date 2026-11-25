"""Run1374: ActionAudit reparse-policy guard self-custody."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.agency.audit as audit
from ark.agency.audit import ActionAuditSchemaError


def test_replaced_audit_reparse_guard_is_rejected_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lstat_calls: list[Path] = []

    def forbidden_lstat(path: Path):
        lstat_calls.append(path)
        raise AssertionError("filesystem inspected after audit guard replacement")

    with monkeypatch.context() as patch:
        patch.setattr(audit, "_require_original_reparse_policy", lambda: None)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            ActionAuditSchemaError,
            match="audit reparse-point policy changed",
        ):
            audit._require_safe_audit_path(
                tmp_path / "action-audit.sqlite3",
                allow_new_parents=False,
            )

    assert lstat_calls == []


def test_reentrant_audit_reparse_guard_replacement_is_rejected_after_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat
    lstat_calls: list[Path] = []

    def replace_guard_after_lstat(path: Path):
        lstat_calls.append(path)
        metadata = original_lstat(path)
        patch.setattr(audit, "_require_original_reparse_policy", lambda: None)
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", replace_guard_after_lstat)
        with pytest.raises(
            ActionAuditSchemaError,
            match="audit reparse-point policy changed",
        ):
            audit._require_safe_audit_path(
                tmp_path / "action-audit.sqlite3",
                allow_new_parents=False,
            )

    assert len(lstat_calls) == 1
