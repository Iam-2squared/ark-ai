"""ActionAudit path admission pins the stat predicates it relies on.

Synthetic in-process substitutions only; no audit database or external action
is opened or performed.
"""

from __future__ import annotations

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
