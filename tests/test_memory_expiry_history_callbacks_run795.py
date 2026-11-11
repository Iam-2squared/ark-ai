"""The expiry reviewer cannot skip either mandatory history validator.

Synthetic SQLite only; no actual purge, deletion or private disclosure.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import expiry_candidate_preview as expiry


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "synthetic-expiry.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "private")
    store.put(
        MemoryWrite(scope, "synthetic", "fixture-only", expires_at_ms=1200),
    )
    report = expiry.review_memory_expiry_candidates(
        store, scope, now_ms=1500, limit=100,
    )
    assert report.candidate_count == 1
    return store, scope, report


def _check(phase, store, scope, report):
    if phase == "preview":
        return expiry.review_memory_expiry_candidates(
            store, scope, now_ms=1500, limit=100,
        )
    return expiry.verify_memory_expiry_preview(
        report, store, scope, now_ms=1500, limit=100,
        retained_preview_sha256=report.preview_sha256,
    )


@pytest.mark.parametrize("phase", ("preview", "verify"))
@pytest.mark.parametrize("checker", (
    "_check_global_event_highwater", "_check_due_event_chain",
))
def test_replaced_mandatory_history_check_rejected_before_private_sqlite(
    tmp_path, monkeypatch, phase, checker,
):
    store, scope, report = _fixture(tmp_path)
    opened = []
    called = []

    def forbidden_open(*_args, **_kwargs):
        opened.append(True)
        raise AssertionError("private SQLite was opened")

    def skipped_history(*_args, **_kwargs):
        called.append(True)
        return 0

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden_open)
        patch.setattr(expiry, checker, skipped_history)
        with pytest.raises(
            expiry.MemoryExpiryPreviewRejected, match="digest protocol",
        ):
            _check(phase, store, scope, report)
    assert opened == []
    assert called == []


@pytest.mark.parametrize("phase", ("preview", "verify"))
@pytest.mark.parametrize(("name", "value"), (
    ("_MAX_ROWS", 1001),
    ("_MAX_EVENT_SCAN", 40001),
    ("_MAX_TIME", 2**63),
))
def test_replaced_expiry_limits_rejected_before_private_sqlite(
    tmp_path, monkeypatch, phase, name, value,
):
    store, scope, report = _fixture(tmp_path)
    opened = []

    def forbidden_open(*_args, **_kwargs):
        opened.append(True)
        raise AssertionError("private SQLite was opened")

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden_open)
        patch.setattr(expiry, name, value)
        with pytest.raises(
            expiry.MemoryExpiryPreviewRejected, match="digest protocol",
        ):
            _check(phase, store, scope, report)
    assert opened == []


def test_original_history_checks_remain_mandatory_and_non_authorizing(tmp_path):
    store, scope, report = _fixture(tmp_path)
    assert _check("preview", store, scope, report) == report
    assert _check("verify", store, scope, report) is None
    assert report.deletion_authorized is False
    assert report.owner_consent_authenticated is False
    assert report.trusted_clock_verified is False
