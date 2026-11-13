"""Audit SQLite preflight rejects oversized encoded paths before inventory.

These synthetic path guards do not authenticate historical audit events.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.agency import audit


@pytest.mark.parametrize("absolute", (True, False))
def test_encoded_audit_path_rejected_before_local_file_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, absolute: bool,
) -> None:
    source = (
        tmp_path / ("界" * 1400 + ".sqlite3")
        if absolute else Path("界" * 1400 + ".sqlite3")
    )
    assert len(str(source)) < 4096
    assert len(os.fsencode(source)) > 4096

    def forbid_lstat(_self: Path) -> object:
        raise AssertionError("oversized Audit fixture reached filesystem inventory")

    with monkeypatch.context() as patched:
        patched.setattr(Path, "lstat", forbid_lstat)
        with pytest.raises(audit.ActionAuditSchemaError, match="local fixture limits"):
            audit._require_safe_audit_path(source, allow_new_parents=True)


def test_normal_audit_fixture_path_passes_preflight(tmp_path: Path) -> None:
    audit._require_safe_audit_path(
        tmp_path / "audit.sqlite3", allow_new_parents=True,
    )
