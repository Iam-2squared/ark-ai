"""Fail closed on replaced privacy inventory callbacks before private row reads.

These tests use only synthetic local SQLite records. They do not authorize
erasure, real personal-context reuse or external data access.
"""

from __future__ import annotations

import pytest
from test_personal_context_retention_review_run376 import _review, _setup

import ark.personal_context_retention_review as retention
from ark.memory.sqlite_store import SQLiteMemoryStore


@pytest.mark.parametrize(
    "dependency",
    (
        "_record",
        "_validate_v1_schema",
        "_scope_digest",
        "review_revocation_continuity",
        "hashlib.sha256",
        "json.dumps",
    ),
)
def test_poisoned_dependency_rejected_without_callback(
    tmp_path, monkeypatch, dependency,
):
    state = _setup(tmp_path)
    executed = []

    def poison(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("unreviewed callback may receive private evidence")

    if dependency == "hashlib.sha256":
        monkeypatch.setattr(retention.hashlib, "sha256", poison)
    elif dependency == "json.dumps":
        monkeypatch.setattr(retention.json, "dumps", poison)
    else:
        monkeypatch.setattr(retention, dependency, poison)

    with pytest.raises(
        retention.SyntheticRetentionRejected, match="dependency changed",
    ):
        _review(state)
    assert executed == []


def test_dependency_replacement_during_connection_denied_before_row_callback(
    tmp_path, monkeypatch,
):
    state = _setup(tmp_path)
    open_original = SQLiteMemoryStore._connect_readonly
    inspected = []

    def poison_row(row):
        inspected.append(row)
        raise AssertionError("private Memory row reached a replaced callback")

    def replaced_open(self):
        # Simulate a reentrant transition after the initial contract check,
        # before a private Memory row reaches the original _record parser.
        monkeypatch.setattr(retention, "_record", poison_row)
        return open_original(self)

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", replaced_open)
    with pytest.raises(
        retention.SyntheticRetentionRejected, match="dependency changed",
    ):
        _review(state)
    assert inspected == []


def test_original_callbacks_remain_content_minimized_and_denial_only(tmp_path):
    report = _review(_setup(tmp_path))
    assert len(report.items) == 4
    assert report.expired_count == 2
    assert report.erasure_completed is False
    assert report.deletion_authorized is False
    assert report.context_use_authorized is False
    assert "private-test-fixture" not in repr(report)
