"""Bounded, privacy-safe ActionAudit outcome labels on synthetic SQLite only."""

from __future__ import annotations

import sqlite3

import pytest

import ark.agency.audit as audit_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call(number: int = 1) -> ToolCall:
    return ToolCall(
        "fixture.audit", "fixture.read", "synthetic:scope", {"number": number},
    )


@pytest.mark.parametrize(
    "outcome",
    (
        "", " ", "x" * 257, "é" * 129, "line\nbreak", "c1\u0085",
        "bidi\u202e", "\u0600", "\u070f", "\ufff9", "\U000e0001",
        "\ud800", None, True,
    ),
)
def test_invalid_outcome_is_rejected_before_database_or_clock(
    tmp_path, monkeypatch, outcome,
):
    clock_calls = []
    audit = SQLiteActionAudit(
        tmp_path / "audit.sqlite3",
        clock_ms=lambda: clock_calls.append(True) or 100,
    )

    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("invalid outcome must be rejected before SQLite")

    monkeypatch.setattr(audit, "_connect", forbidden_connect)
    with pytest.raises(ValueError):
        audit.append(_call(), outcome=outcome)
    assert clock_calls == []


def test_unicode_category_dependency_substitution_fails_closed_before_database_or_clock(
    tmp_path, monkeypatch,
):
    clock_calls = []
    audit = SQLiteActionAudit(
        tmp_path / "audit.sqlite3",
        clock_ms=lambda: clock_calls.append(True) or 100,
    )

    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("changed Unicode dependency must be rejected before SQLite")

    monkeypatch.setattr(audit, "_connect", forbidden_connect)
    monkeypatch.setattr(audit_module.unicodedata, "category", lambda _value: "Cc")

    with pytest.raises(ActionAuditSchemaError, match="Unicode category dependency changed"):
        audit.append(_call(), outcome="\u0600")
    assert clock_calls == []


def test_bounded_unicode_outcome_at_utf8_byte_boundary_round_trips(tmp_path):
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=lambda: 100)
    outcome = "é" * 128  # 128 code points, exactly 256 UTF-8 bytes.
    event = audit.append(_call(), outcome=outcome)
    assert event.outcome == outcome
    assert audit.events() == [event]


@pytest.mark.parametrize(
    "outcome",
    ("x" * 257, "line\nbreak", "bidi\u202e", "\u0600", "\ufff9", "\U000e0001"),
)
def test_corrupt_persisted_outcome_fails_closed_without_clock_or_repair(
    tmp_path, outcome,
):
    path = tmp_path / "audit.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    audit.append(_call(), outcome="synthetic-safe")
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE action_events SET outcome=? WHERE event_id=1",
            (outcome,),
        )
        before = conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall()

    clock_calls = []
    reopened = SQLiteActionAudit(
        path, clock_ms=lambda: clock_calls.append(True) or 101,
    )
    with pytest.raises(ActionAuditSchemaError):
        reopened.events()
    with pytest.raises(ActionAuditSchemaError):
        reopened.append(_call(2), outcome="synthetic-next")
    assert clock_calls == []
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT * FROM action_events ORDER BY event_id"
        ).fetchall() == before
