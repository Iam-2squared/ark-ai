"""Registered READ joins must recheck child receipt bytes after denial callbacks.

This module uses only disconnected fixture tools, local SQLite, and a
forbidden backend. A False-valued property may still mutate a frozen child.
"""

from __future__ import annotations

import pytest
from test_recovered_registered_read_join_run550 import invoke, make_case

import ark.agency.disconnected_recovered_registered_read_join as joined


@pytest.mark.parametrize(
    "denial",
    ("backend_dispatched", "dependencies_completed_proven"),
)
def test_false_child_denial_cannot_rewrite_hash_before_parent_join(
    tmp_path, monkeypatch, denial,
):
    case = make_case(tmp_path)
    child_type = joined.RegisteredBatchReceiptReview
    original_getter = getattr(child_type, denial)
    original_review = joined.review_registered_batch_receipt

    def mutate_during_denial(child):
        object.__setattr__(child, "review_sha256", "0" * 64)
        return False

    def review_then_swap(*args, **kwargs):
        # Restore the genuine implementation for the independent child
        # review; only the returned receipt is attacked by its own getter.
        monkeypatch.setattr(child_type, denial, original_getter)
        child = original_review(*args, **kwargs)
        monkeypatch.setattr(child_type, denial, property(mutate_during_denial))
        return child

    monkeypatch.setattr(
        joined, "review_registered_batch_receipt", review_then_swap,
    )
    try:
        with pytest.raises(
            joined.RecoveredRegisteredReadRejected,
            match="registered child changed during denial callbacks",
        ):
            invoke(case)
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


@pytest.mark.parametrize(
    "states",
    (("SUCCEEDED", "SUCCEEDED"), ("SUCCEEDED", "FAILED")),
)
def test_unchanged_registered_receipts_still_join_without_replay(tmp_path, states):
    case = make_case(tmp_path, states)
    try:
        result = invoke(case)
        assert len(result.registered_steps) == states.count("SUCCEEDED")
        assert result.backend_dispatched is False
        assert result.automatic_replay_authorized is False
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()
