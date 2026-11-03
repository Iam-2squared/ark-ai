"""Manual Memory COMMIT triage must retain the exact original CAS token.

No stored row is modified and no previous uncertain update is retried. An
equal-valued reflected token replacement is still a new review-input epoch.
"""

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import postcommit_uncertainty_review as module


def _clone(value):
    clone = value.encode("ascii").decode("ascii")
    assert clone == value and clone is not value
    return clone


@pytest.mark.parametrize(
    "field", ("memory_id", "event_prefix_sha256", "row_sha256"),
)
def test_snapshot_callback_cannot_rebase_equal_retained_token_carrier(
    tmp_path, monkeypatch, field,
):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    original = module._snapshot
    calls = []

    def swapped(conn, memory_id, requested_scope, source_id):
        observed = original(conn, memory_id, requested_scope, source_id)
        old = getattr(retained, field)
        object.__setattr__(retained, field, _clone(old))
        calls.append(field)
        return observed

    monkeypatch.setattr(module, "_snapshot", swapped)
    with pytest.raises(
        module.MemoryCommitTriageRejected, match="manual review",
    ):
        module.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )
    assert calls == [field]
    assert store.get(saved.memory_id, scope).revision == 1
    assert len(store.events(scope)) == 1


def test_untouched_retained_token_returns_no_retry_review(tmp_path):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    review = module.review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert review.disposition == "LOCAL_UNCHANGED"
    assert review.automatic_retry_authorized is False
    assert review.write_authorized is False
    assert review.caller_attribution_proven is False
    assert store.get(saved.memory_id, scope).revision == 1
    assert len(store.events(scope)) == 1
