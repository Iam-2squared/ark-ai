"""Detached Memory delta results cannot acquire authority or mutate late."""

from __future__ import annotations

import pytest

import ark.offline_memory_delta as memory


def _claims():
    row = memory.OfflineMemoryRowClaim(
        "mem_" + "1" * 16, "b" * 64, "c" * 64, 1, 0, 1000,
    )
    before = memory.OfflineMemorySnapshotClaim("a" * 64, 100, (row,))
    after = memory.OfflineMemorySnapshotClaim("a" * 64, 101, (row,))
    return before, after


def _review(before, after):
    return memory.review_offline_memory_delta(
        before,
        after,
        retained_prior_fingerprint=memory.fingerprint_offline_memory_snapshot(before),
        retained_current_fingerprint=memory.fingerprint_offline_memory_snapshot(after),
    )


def test_unchanged_synthetic_review_is_inert_and_deterministic():
    prior, current = _claims()
    result = _review(prior, current)
    assert result == _review(prior, current)
    assert result.unchanged_count == 1
    assert result.source_authenticated is False
    assert result.cross_store_atomicity_verified is False
    assert result.deletion_or_erasure_proven is False
    assert result.tool_dispatch_authorized is False


def test_constructor_replacement_cannot_claim_verified_custody(monkeypatch):
    prior, current = _claims()
    monkeypatch.setattr(memory, "OfflineMemoryDeltaReview", lambda *args: object())
    with pytest.raises(memory.OfflineMemoryDeltaRejected, match="constructed Memory"):
        _review(prior, current)


@pytest.mark.parametrize(
    "name",
    (
        "source_authenticated",
        "cross_store_atomicity_verified",
        "deletion_or_erasure_proven",
        "tool_dispatch_authorized",
    ),
)
def test_exact_result_authority_getter_must_remain_false(monkeypatch, name):
    prior, current = _claims()
    monkeypatch.setattr(memory._REVIEW_TYPE, name, property(lambda self: True))
    with pytest.raises(memory.OfflineMemoryDeltaRejected, match="claims authority"):
        _review(prior, current)


@pytest.mark.parametrize("target", ("result", "source"))
def test_late_false_authority_getter_cannot_mutate_delta(monkeypatch, target):
    prior, current = _claims()

    def poison(result):
        if target == "result":
            object.__setattr__(result, "delta_fingerprint", "f" * 64)
        else:
            object.__setattr__(prior, "owner_sha256", "f" * 64)
        return False

    monkeypatch.setattr(
        memory._REVIEW_TYPE, "tool_dispatch_authorized", property(poison),
    )
    with pytest.raises(memory.OfflineMemoryDeltaRejected, match="changed"):
        _review(prior, current)
