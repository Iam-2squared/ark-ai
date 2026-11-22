"""SQLiteActionAudit keeps its local source path identity fixed."""

from __future__ import annotations

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _audit(tmp_path):
    return SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=lambda: 120)


def _call() -> ToolCall:
    return ToolCall("mock", "cap", "fixture", {"secret": "not-in-audit"})


def test_path_slot_rejects_ordinary_assignment_and_deletion(tmp_path) -> None:
    audit = _audit(tmp_path)
    original = audit.path

    with pytest.raises(AttributeError, match="path identity"):
        audit.path = tmp_path / "alternate.sqlite3"
    with pytest.raises(AttributeError, match="path identity"):
        del audit.path

    assert audit.path is original
    assert "path" not in vars(audit)
    assert len(audit.events()) == 0


def test_instance_dictionary_cannot_shadow_source_path(tmp_path) -> None:
    audit = _audit(tmp_path)
    alternate = tmp_path / "alternate.sqlite3"
    audit.__dict__["path"] = alternate

    with pytest.raises(ActionAuditSchemaError, match="path changed"):
        audit.events()

    assert not alternate.exists()


def test_reflective_pre_call_retarget_is_rejected_before_open(tmp_path) -> None:
    audit = _audit(tmp_path)
    alternate = tmp_path / "alternate.sqlite3"
    object.__setattr__(audit, "path", alternate)

    with pytest.raises(ActionAuditSchemaError, match="path changed"):
        audit.events()

    assert not alternate.exists()


def test_reentrant_connect_cannot_retarget_source_before_append(
    tmp_path, monkeypatch,
) -> None:
    audit = _audit(tmp_path)
    alternate = tmp_path / "alternate.sqlite3"
    original_connect = audit._connect

    def retargeting_connect(*, create: bool = False):
        object.__setattr__(audit, "path", alternate)
        return original_connect(create=create)

    monkeypatch.setattr(audit, "_connect", retargeting_connect)
    with pytest.raises(ActionAuditSchemaError, match="path changed"):
        audit.append(_call(), outcome="must-not-append")

    assert not alternate.exists()


def test_subclass_is_rejected_before_parent_or_database_creation(tmp_path) -> None:
    class DerivedAudit(SQLiteActionAudit):
        pass

    target = tmp_path / "not-created" / "audit.sqlite3"
    with pytest.raises(ActionAuditSchemaError, match="exact SQLiteActionAudit"):
        DerivedAudit(target)

    assert not target.parent.exists()


def test_normal_append_and_read_keep_original_path(tmp_path) -> None:
    audit = _audit(tmp_path)
    original = audit.path

    event = audit.append(_call(), outcome="fixture")
    assert event.event_id == 1
    assert len(audit.events()) == 1
    assert audit.path is original
    assert "path" not in vars(audit)
