"""Ordered Memory witness continuity, retaining all unresolved trust boundaries."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.memory.retained_epoch_chain as chain
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview
from ark.memory.contracts import MemorySchemaError

_SCOPE = ("a" * 64,)


def _epoch(count=1, tail=None, *, content="b", clock="c", rows=1):
    return AtomicMemoryEpochReview(
        _SCOPE, (rows,), (count,), (count if tail is None else tail,),
        clock * 64, content * 64,
    )


def test_three_independent_unchanged_local_observations():
    result = chain.review_retained_memory_chain((
        _epoch(clock="1"), _epoch(clock="2"), _epoch(clock="3"),
    ))
    assert result.observations == 3
    assert result.added_event_counts == (0,)
    assert result.status == "UNCHANGED_LOCAL_CONTENT"
    assert len(result.chain_digest) == 64
    assert result.historical_prefix_proven is False
    assert result.independent_writer_proven is False
    assert result.custody_authenticated is False
    assert result.memory_disclosure_authorized is False
    assert result.dispatch_authorized is False


def test_multiple_appends_accumulate_but_never_prove_prefix():
    report = chain.review_retained_memory_chain((
        _epoch(1), _epoch(2, content="d"), _epoch(4, content="e"),
    ))
    assert report.added_event_counts == (3,)
    assert report.status == "ADVANCED_HISTORY_UNVERIFIED"
    assert report.historical_prefix_proven is False


def test_intermediate_observation_is_part_of_chain_digest():
    a, c = _epoch(1), _epoch(3, content="e")
    first = chain.review_retained_memory_chain((
        a, _epoch(2, content="d"), c,
    ))
    second = chain.review_retained_memory_chain((
        a, _epoch(2, content="f"), c,
    ))
    assert first.chain_digest != second.chain_digest


def test_stale_or_rolled_back_intermediate_epoch_rejected():
    with pytest.raises(MemorySchemaError, match="regressed"):
        chain.review_retained_memory_chain((
            _epoch(1), _epoch(3, content="d"), _epoch(2, content="e"),
        ))


def test_same_count_rewrite_at_intermediate_epoch_rejected():
    with pytest.raises(MemorySchemaError, match="content changed"):
        chain.review_retained_memory_chain((
            _epoch(1), _epoch(1, content="d"), _epoch(2, content="e"),
        ))


def test_scope_retarget_denied_even_with_plausible_hashes():
    forged = replace(_epoch(2), scope_fingerprints=("f" * 64,))
    with pytest.raises(MemorySchemaError, match="scope identity"):
        chain.review_retained_memory_chain((_epoch(1), forged))


@pytest.mark.parametrize("input_epochs", [
    (),
    (_epoch(),),
    [_epoch(), _epoch()],
    (_epoch(),) * 2,
    (_epoch(),) * 17,
    (_epoch(), object()),
])
def test_exact_bounded_distinct_input_required(input_epochs):
    with pytest.raises(MemorySchemaError, match="exact independent"):
        chain.review_retained_memory_chain(input_epochs)


def test_non_exact_boolean_event_counts_are_denied():
    with pytest.raises(MemorySchemaError, match="invalid retained"):
        chain.review_retained_memory_chain((
            _epoch(), replace(_epoch(), event_counts=(True,)),
        ))


def test_replacement_of_prior_source_during_later_edge_rejected(monkeypatch):
    a, b, c = _epoch(1), _epoch(2, content="d"), _epoch(3, content="e")
    original = chain.review_retained_memory_epoch
    calls = 0

    def mutate(previous, current):
        nonlocal calls
        compared = original(previous, current)
        calls += 1
        if calls == 2:
            object.__setattr__(a, "content_digest", "f" * 64)
        return compared

    monkeypatch.setattr(chain, "review_retained_memory_epoch", mutate)
    with pytest.raises(MemorySchemaError, match="carrier changed"):
        chain.review_retained_memory_chain((a, b, c))


def test_replaced_comparison_cannot_claim_authority(monkeypatch):
    monkeypatch.setattr(
        chain, "review_retained_memory_epoch", lambda *args: object(),
    )
    with pytest.raises(MemorySchemaError, match="edge result changed"):
        chain.review_retained_memory_chain((_epoch(), _epoch(clock="d")))


def test_replaced_chain_result_cannot_claim_dispatch(monkeypatch):
    monkeypatch.setattr(
        chain, "RetainedMemoryChainReview", lambda *args: object(),
    )
    with pytest.raises(MemorySchemaError, match="chain result changed"):
        chain.review_retained_memory_chain((_epoch(), _epoch(clock="d")))
