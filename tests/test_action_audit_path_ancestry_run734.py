"""Synthetic audit file custody: reject symbolic ancestors and foreign links.

All tests use disposable local SQLite and synthetic ToolCall arguments.
An audit event is not a trusted clock, authenticated provenance or real action.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall

CALL = ToolCall("fixture", "audit", "local", {"n": 1})


def test_nested_new_parent_bootstraps_then_reopens_without_dispatch(tmp_path: Path):
    path = tmp_path / "new" / "deep" / "audit.sqlite"
    first = SQLiteActionAudit(path, clock_ms=lambda: 100)
    assert first.events() == []
    event = first.append(CALL, outcome="synthetic-only")
    assert event.event_id == 1
    second = SQLiteActionAudit(path, clock_ms=lambda: 101)
    assert second.events() == [event]


def test_symbolic_grandparent_cannot_create_or_reopen_audit(tmp_path: Path):
    real = tmp_path / "real"
    deep = real / "deep"
    deep.mkdir(parents=True)
    audit_path = deep / "original.sqlite"
    first = SQLiteActionAudit(audit_path, clock_ms=lambda: 100)
    original = first.append(CALL, outcome="synthetic")
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"directory symlink unavailable: {exc}")
    with pytest.raises(ActionAuditSchemaError, match="ancestor"):
        SQLiteActionAudit(alias / "deep" / "other.sqlite", clock_ms=lambda: 110)
    assert not (deep / "other.sqlite").exists()
    with pytest.raises(ActionAuditSchemaError, match="ancestor"):
        SQLiteActionAudit(alias / "deep" / "original.sqlite", clock_ms=lambda: 110)
    assert first.events() == [original]


@pytest.mark.parametrize("method", ("append", "events"))
def test_late_symlinked_source_is_not_followed(tmp_path: Path, method: str):
    original = tmp_path / "original.sqlite"
    audit = SQLiteActionAudit(original, clock_ms=lambda: 100)
    alternate = tmp_path / "alternate.sqlite"
    SQLiteActionAudit(alternate, clock_ms=lambda: 100)
    try:
        redirected = tmp_path / "redirected.sqlite"
        redirected.symlink_to(alternate)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"file symlink unavailable: {exc}")
    audit.path = redirected
    with pytest.raises(ActionAuditSchemaError, match="symbolic"):
        if method == "append":
            audit.append(CALL, outcome="never")
        else:
            audit.events()
    assert SQLiteActionAudit(alternate).events() == []
    audit.path = original
    assert audit.events() == []


@pytest.mark.parametrize("method", ("bootstrap", "read"))
def test_parent_traversal_never_aliases_audit(tmp_path: Path, method: str):
    (tmp_path / "dir").mkdir()
    path = tmp_path / "dir" / ".." / "escaped.sqlite"
    with pytest.raises(ActionAuditSchemaError, match="parent traversal"):
        if method == "bootstrap":
            SQLiteActionAudit(path)
        else:
            initial = SQLiteActionAudit(tmp_path / "safe.sqlite")
            initial.path = path
            initial.events()
    assert not (tmp_path / "escaped.sqlite").exists()


def test_hardlinked_audit_file_denied_before_sqlite(tmp_path: Path):
    original = tmp_path / "original.sqlite"
    audit = SQLiteActionAudit(original)
    alias = tmp_path / "alias.sqlite"
    try:
        os.link(original, alias)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"hardlinks unavailable: {exc}")
    with pytest.raises(ActionAuditSchemaError, match="one regular-file link"):
        SQLiteActionAudit(alias)
    with pytest.raises(ActionAuditSchemaError, match="one regular-file link"):
        audit.events()


def test_file_in_place_of_parent_cannot_create_database(tmp_path: Path):
    blocker = tmp_path / "blocker"
    blocker.write_bytes(b"no directory here")
    with pytest.raises(ActionAuditSchemaError, match="ancestor"):
        SQLiteActionAudit(blocker / "audit.sqlite")
    assert blocker.read_bytes() == b"no directory here"


def test_custom_pathlike_callbacks_are_rejected_before_evaluation():
    calls = []

    class HostilePath:
        def __fspath__(self):
            calls.append("executed")
            raise AssertionError("untrusted path callback")

    with pytest.raises(ActionAuditSchemaError, match="exact local path"):
        SQLiteActionAudit(HostilePath())
    assert calls == []
