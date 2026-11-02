"""A post-COMMIT triage report must match the observed SQLite row image.

All writes below are to a temporary local SQLite fixture, not an external
ToolBackend. A matching row cannot prove which caller committed it.
"""

from __future__ import annotations

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import MemoryWrite
from ark.memory import postcommit_uncertainty_review as triage
from ark.memory.generation_fenced_cas import generation_fenced_memory_update


@pytest.mark.parametrize("changed_field", ("content", "metadata", "expires_at_ms"))
def test_late_row_image_rewrite_cannot_forge_one_matching_update(
    tmp_path, monkeypatch, changed_field,
):
    store, scope, _, retained, proposed = make_case(tmp_path)
    if changed_field == "content":
        actual = MemoryWrite(
            scope, "stable", "a different update", metadata=dict(proposed.metadata),
        )
    elif changed_field == "metadata":
        actual = MemoryWrite(
            scope, "stable", proposed.content, metadata={"source": "different"},
        )
    else:
        actual = MemoryWrite(
            scope, "stable", proposed.content, metadata=dict(proposed.metadata),
            expires_at_ms=1500,
        )
    generation_fenced_memory_update(store, actual, retained=retained)

    original_snapshot = triage._snapshot
    original_digest = triage._digest
    observed_rows = []
    tampered = []

    def capture_row(*args, **kwargs):
        row, token = original_snapshot(*args, **kwargs)
        observed_rows.append(row)
        return row, token

    def rewrite_after_sql_snapshot(domain, fields):
        if domain == triage._EVENT_DOMAIN and not tampered:
            row = observed_rows[-1]
            object.__setattr__(
                row, changed_field, getattr(proposed, changed_field),
            )
            tampered.append(changed_field)
        return original_digest(domain, fields)

    monkeypatch.setattr(triage, "_snapshot", capture_row)
    monkeypatch.setattr(triage, "_digest", rewrite_after_sql_snapshot)
    with pytest.raises(triage.MemoryCommitTriageRejected):
        triage.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )
    assert tampered == [changed_field]
    assert len(observed_rows) == 1
    assert [event.operation for event in store.events(scope)] == [
        "create", "update",
    ]


def test_connection_teardown_cannot_change_row_after_classification(
    tmp_path, monkeypatch,
):
    store, scope, _, retained, proposed = make_case(tmp_path)
    generation_fenced_memory_update(store, proposed, retained=retained)
    real_snapshot = triage._snapshot
    real_closing = triage.closing
    observed_rows = []
    tampered = []

    def remember_row(*args, **kwargs):
        row, token = real_snapshot(*args, **kwargs)
        observed_rows.append(row)
        return row, token

    def close_then_mutate(conn):
        context = real_closing(conn)

        class ClosingWithMutation:
            def __enter__(self):
                return context.__enter__()

            def __exit__(self, exception, error, tb):
                closed = context.__exit__(exception, error, tb)
                object.__setattr__(observed_rows[-1], "content", "not the update")
                tampered.append(True)
                return closed

        return ClosingWithMutation()

    monkeypatch.setattr(triage, "_snapshot", remember_row)
    monkeypatch.setattr(triage, "closing", close_then_mutate)
    with pytest.raises(triage.MemoryCommitTriageRejected):
        triage.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )
    assert tampered == [True]
    assert store.get(next(iter(store.events(scope))).memory_id, scope).content == (
        proposed.content
    )


def test_unmodified_row_still_yields_manual_only_match(tmp_path):
    store, scope, _, retained, proposed = make_case(tmp_path)
    generation_fenced_memory_update(store, proposed, retained=retained)
    report = triage.review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert report.disposition == "ONE_MATCHING_UPDATE_VISIBLE"
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.caller_attribution_proven is False
