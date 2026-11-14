"""Audit continuity refuses reentrant drift before its first SQLite SELECT.

These are read-only local fixtures. A coherent audit prefix does not attest
real backend execution, a trusted clock, or authenticated human approval.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.agency.audit_continuity_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _setup(tmp_path):
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    call = ToolCall("fixture", "write", "local", {"a": 1})
    audit.append(call, outcome="only-local")
    return audit, call


@pytest.mark.parametrize("boundary", ("resolve", "as_uri", "connect"))
@pytest.mark.parametrize("change", ("source", "retained"))
def test_open_boundary_refuses_a_changed_source_or_retained_witness(
    tmp_path, monkeypatch, boundary, change,
):
    audit, _call = _setup(tmp_path)
    retained = module.review_audit_continuity(audit)
    source_epoch = audit.path
    invoked = []
    connections = []

    def drift():
        if change == "source":
            audit.path = Path(str(source_epoch))
        else:
            object.__setattr__(retained, "event_count", 2)

    if boundary == "connect":
        original = sqlite3.connect

        def connecting(*args, **kwargs):
            conn = original(*args, **kwargs)
            if "audit.sqlite" in str(args[0]) and "mode=ro" in str(args[0]):
                invoked.append("connect")
                connections.append(conn)
                drift()
            return conn

        monkeypatch.setattr(module.sqlite3, "connect", connecting)
    else:
        original = getattr(Path, boundary)

        def hooked(path, *args, **kwargs):
            value = original(path, *args, **kwargs)
            matches = (
                path is source_epoch if boundary == "resolve"
                else path == source_epoch
            )
            if matches:
                invoked.append(boundary)
                drift()
            return value

        monkeypatch.setattr(Path, boundary, hooked)

    with pytest.raises(
        ActionAuditSchemaError, match="source changed|witness changed",
    ):
        module.review_audit_continuity(audit, retained=retained)
    assert invoked == [boundary]
    for conn in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
            conn.execute("SELECT 1")


def test_stable_open_returns_the_same_readonly_witness(tmp_path):
    audit, call = _setup(tmp_path)
    retained = module.review_audit_continuity(audit)
    result = module.review_audit_continuity(audit, retained=retained)
    assert result == retained
    assert result.event_count == 1
    assert audit.events()[0].request_id == call.request_id


def test_missing_source_is_never_created_while_reviewing(tmp_path):
    audit, _call = _setup(tmp_path)
    lost = tmp_path / "missing.sqlite"
    audit.path = lost
    with pytest.raises(ActionAuditSchemaError, match="cannot read"):
        module.review_audit_continuity(audit)
    assert not lost.exists()


def test_readonly_review_rejects_a_stale_prefix_after_restart(tmp_path):
    audit, call = _setup(tmp_path)
    retained = module.review_audit_continuity(audit)
    reopened = SQLiteActionAudit(audit.path, clock_ms=lambda: 13)
    reopened.append(call, outcome="second synthetic event")
    result = module.review_audit_continuity(reopened, retained=retained)
    assert result.event_count == 2
    assert result.tail_event_id == 2
    assert result != retained
