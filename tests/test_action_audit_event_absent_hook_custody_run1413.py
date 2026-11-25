"""Run1413: ActionAudit event guards distinguish absent class hooks."""

from __future__ import annotations

import subprocess
import sys

import pytest

import ark.agency.audit as audit_module
from ark.agency.contracts import ActionAuditSchemaError, ToolCall

_LOOKUP_HOOKS = ("__getattribute__", "__getattr__")


def _case(tmp_path):
    audit = audit_module.SQLiteActionAudit(
        tmp_path / "audit.sqlite", clock_ms=lambda: 100,
    )
    call = ToolCall("fixture.read", "fixture.read", "fixture:scope", {"n": 1})
    return audit, call


def _replace_class_entry(
    carrier: type,
    name: str,
    replacement: object,
) -> tuple[bool, object | None]:
    namespace = vars(carrier)
    original = (name in namespace, namespace.get(name))
    type.__setattr__(carrier, name, replacement)
    return original


def _restore_class_entry(
    carrier: type,
    name: str,
    original: tuple[bool, object | None],
) -> None:
    was_present, value = original
    if was_present:
        type.__setattr__(carrier, name, value)
    else:
        type.__delattr__(carrier, name)


@pytest.mark.parametrize("hook", _LOOKUP_HOOKS)
@pytest.mark.parametrize("replacement_kind", ("explicit-none", "sentinel-installed"))
def test_absent_event_lookup_hooks_require_namespace_absence_before_sqlite(
    tmp_path,
    hook,
    replacement_kind,
):
    audit, call = _case(tmp_path)
    connection_calls = []

    def forbidden_connect():
        connection_calls.append(True)
        raise AssertionError("SQLite access must follow ActionAudit carrier validation")

    audit._connect = forbidden_connect
    replacement = (
        None
        if replacement_kind == "explicit-none"
        else audit_module._ABSENT_EVENT_CLASS_HOOK
    )
    original = _replace_class_entry(
        audit_module.ActionAuditEvent, hook, replacement,
    )
    try:
        with pytest.raises(
            ActionAuditSchemaError, match="audit event constructor changed",
        ):
            audit.append(call, outcome="recorded")
    finally:
        _restore_class_entry(audit_module.ActionAuditEvent, hook, original)

    assert connection_calls == []


@pytest.mark.parametrize("replacement_kind", ("explicit-none", "sentinel-installed"))
def test_absent_event_new_hook_is_rejected_in_an_isolated_process(
    replacement_kind,
):
    # __new__ changes CPython's allocation slot; isolate each probe so no
    # interpreter-level slot state can leak into the surrounding pytest run.
    script = f"""
import ark.agency.audit as audit_module
from ark.agency.contracts import ActionAuditSchemaError

replacement = (
    None
    if {replacement_kind!r} == "explicit-none"
    else audit_module._ABSENT_EVENT_CLASS_HOOK
)
type.__setattr__(audit_module.ActionAuditEvent, "__new__", replacement)
try:
    audit_module._require_original_event_constructor()
except ActionAuditSchemaError:
    pass
else:
    raise SystemExit("absent __new__ substitution was accepted")
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_replaced_absence_sentinel_is_rejected(monkeypatch):
    monkeypatch.setattr(audit_module, "_ABSENT_EVENT_CLASS_HOOK", object())
    with pytest.raises(
        ActionAuditSchemaError, match="audit event constructor changed",
    ):
        audit_module._require_original_event_constructor()


def test_joint_public_and_private_event_type_replacement_is_rejected(
    monkeypatch,
):
    replacement = type("ReplacementActionAuditEvent", (), {})
    monkeypatch.setattr(audit_module, "ActionAuditEvent", replacement)
    monkeypatch.setattr(audit_module, "_EVENT_TYPE", replacement)
    with pytest.raises(
        ActionAuditSchemaError, match="audit event constructor changed",
    ):
        audit_module._require_original_event_constructor()


def test_original_event_class_epoch_remains_valid():
    audit_module._require_original_event_constructor()
