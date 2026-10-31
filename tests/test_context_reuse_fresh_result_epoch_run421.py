"""Context reuse must retain the fresh and revoked carrier epochs to return.

Synthetic SQLite only; neither a retained digest nor a successful review grants
consent, context disclosure, notifications or real ToolBackend execution.
"""

import pytest

import ark.personal_context_reuse_review as reuse
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    review_fresh_nonrevoked_context,
)


def _fixture(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "profile")
    memory.put(MemoryWrite(scope, "fixture-source", "fixture-only content"))
    request = CoherentSnapshotRequest(scope.owner_id, (scope.namespace,))
    policy = ContextSelectionPolicy(4, 4)
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    cached = review_fresh_nonrevoked_context(memory, request, policy, ledger)
    return memory, request, policy, ledger, cached


def _review(state, retained=None):
    return reuse.review_synthetic_context_reuse(
        *state, captured_at_ms=100, now_ms=100, max_age_ms=0,
        retained_revocations=retained,
    )


@pytest.mark.parametrize("target", ("items", "content", "namespace", "provenance_id"))
def test_receipt_constructor_cannot_retarget_fresh_projection(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    reviewer = reuse.review_fresh_nonrevoked_context
    receipt_class = reuse.SyntheticContextReuseReview
    fresh_holder = []

    def project(*args, **kwargs):
        fresh = reviewer(*args, **kwargs)
        fresh_holder.append(fresh)
        return fresh

    def receipt(*args):
        assert len(fresh_holder) == 1
        fresh = fresh_holder[0]
        if target == "items":
            clone = tuple(list(fresh.items))
            assert clone == fresh.items and clone is not fresh.items
            object.__setattr__(fresh, "items", clone)
        else:
            item = fresh.items[0]
            value = getattr(item, target)
            clone = (value + "!")[:-1]
            assert clone == value and clone is not value
            object.__setattr__(item, target, clone)
        return receipt_class(*args)

    monkeypatch.setattr(reuse, "review_fresh_nonrevoked_context", project)
    monkeypatch.setattr(reuse, "SyntheticContextReuseReview", receipt)
    with pytest.raises(reuse.SyntheticContextReuseRejected, match="fresh context changed"):
        _review(state)


@pytest.mark.parametrize("target", ("rows", "witness_id"))
def test_receipt_constructor_cannot_swap_retained_veto_carriers(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    state[3].revoke(MemoryScope("fixture-owner", "other"), at_ms=101)
    retained = review_revocation_continuity(state[3])
    receipt_class = reuse.SyntheticContextReuseReview

    def receipt(*args):
        value = getattr(retained, target)
        clone = (
            tuple(list(value)) if target == "rows"
            else (value + "!")[:-1]
        )
        assert clone == value and clone is not value
        object.__setattr__(retained, target, clone)
        return receipt_class(*args)

    monkeypatch.setattr(reuse, "SyntheticContextReuseReview", receipt)
    with pytest.raises(
        reuse.SyntheticContextReuseRejected,
        match="retained revocation witness changed",
    ):
        _review(state, retained=retained)


def test_unmodified_fresh_and_retained_veto_remain_inert(tmp_path):
    state = _fixture(tmp_path)
    state[3].revoke(MemoryScope("fixture-owner", "other"), at_ms=101)
    retained = review_revocation_continuity(state[3])
    receipt = _review(state, retained=retained)
    assert receipt.context_use_authorized is False
    assert receipt.external_disclosure_authorized is False
    assert receipt.dispatch_authorized is False
    assert "fixture-only content" not in repr(receipt)
