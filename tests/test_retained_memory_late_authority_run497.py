"""Late Memory review getters must not turn retained claims into authority."""

from __future__ import annotations

import pytest

from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview
from ark.memory.contracts import MemorySchemaError
from ark.memory.retained_epoch_chain import (
    RetainedMemoryChainReview,
    review_retained_memory_chain,
)


def fixture_epochs():
    return (
        AtomicMemoryEpochReview(
            ("a" * 64,), (1,), (1,), (1,), "b" * 64, "c" * 64,
        ),
        AtomicMemoryEpochReview(
            ("a" * 64,), (1,), (2,), (2,), "b" * 64, "d" * 64,
        ),
    )


def test_normal_chain_reports_no_source_or_dispatch_authority():
    result = review_retained_memory_chain(fixture_epochs())
    assert result.added_event_counts == (1,)
    assert result.dispatch_authorized is False
    assert result.custody_authenticated is False
    assert result.historical_prefix_proven is False


@pytest.mark.parametrize("mutation", (
    "source", "digest", "counts", "same_value_status",
))
def test_last_false_authority_getter_cannot_mutate_source_or_result(
    monkeypatch, mutation,
):
    epochs = fixture_epochs()

    def side_effect(report):
        if mutation == "source":
            object.__setattr__(epochs[0], "content_digest", "f" * 64)
        elif mutation == "digest":
            object.__setattr__(report, "chain_digest", "0" * 64)
        elif mutation == "counts":
            object.__setattr__(report, "added_event_counts", (0,))
        else:
            old = report.status
            equal = bytes(old, "ascii").decode("ascii")
            assert equal == old and equal is not old
            object.__setattr__(report, "status", equal)
        return False

    monkeypatch.setattr(
        RetainedMemoryChainReview,
        "dispatch_authorized",
        property(side_effect),
    )
    with pytest.raises(MemorySchemaError):
        review_retained_memory_chain(epochs)
