"""Memory retained-chain receipts cannot be replaced after an earlier edge."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.memory.retained_epoch_chain as chain
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview
from ark.memory.contracts import MemorySchemaError


def _epoch(count, content):
    return AtomicMemoryEpochReview(
        ("a" * 64,), (1,), (count,), (count,),
        "b" * 64, content * 64,
    )


@pytest.mark.parametrize(("field", "replacement"), [
    ("comparison_digest", "f" * 64),
    ("status", "UNCHANGED_LOCAL_CONTENT"),
    ("new_event_counts", (0,)),
    ("scope_fingerprints", ("f" * 64,)),
])
def test_earlier_edge_mutated_during_later_comparison_is_rejected(
    monkeypatch, field, replacement,
):
    original = chain.review_retained_memory_epoch
    retained = []

    def changed(previous, current):
        edge = original(previous, current)
        if retained:
            object.__setattr__(retained[0], field, replacement)
        else:
            retained.append(edge)
        return edge

    monkeypatch.setattr(chain, "review_retained_memory_epoch", changed)
    with pytest.raises(MemorySchemaError, match="earlier edge result changed"):
        chain.review_retained_memory_chain((
            _epoch(1, "c"), _epoch(2, "d"), _epoch(3, "e"),
        ))


def test_earlier_edge_mutated_during_chain_result_constructor_is_rejected(monkeypatch):
    original_edge = chain.review_retained_memory_epoch
    original_result = chain.RetainedMemoryChainReview
    retained = []

    def capture(previous, current):
        value = original_edge(previous, current)
        retained.append(value)
        return value

    def tamper(*args, **kwargs):
        result = original_result(*args, **kwargs)
        object.__setattr__(retained[0], "comparison_digest", "f" * 64)
        return result

    monkeypatch.setattr(chain, "review_retained_memory_epoch", capture)
    monkeypatch.setattr(chain, "RetainedMemoryChainReview", tamper)
    with pytest.raises(MemorySchemaError, match="earlier edge result changed"):
        chain.review_retained_memory_chain((
            _epoch(1, "c"), _epoch(2, "d"), _epoch(3, "e"),
        ))


def test_clean_chain_still_reports_unverified_history_without_permissions():
    previous = _epoch(1, "c")
    middle = replace(previous, event_counts=(2,), event_tail_ids=(2,), content_digest="d" * 64)
    current = replace(middle, event_counts=(3,), event_tail_ids=(3,), content_digest="e" * 64)
    result = chain.review_retained_memory_chain((previous, middle, current))
    assert result.observations == 3
    assert result.added_event_counts == (2,)
    assert result.status == "ADVANCED_HISTORY_UNVERIFIED"
    assert result.historical_prefix_proven is False
    assert result.independent_writer_proven is False
    assert result.custody_authenticated is False
    assert result.memory_disclosure_authorized is False
    assert result.dispatch_authorized is False
