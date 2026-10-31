"""Pure synthetic epochs: explicit denied authority and rollback checks."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from ark.disconnected_epoch_vector import (
    DisconnectedEpochVector,
    DisconnectedStoreEpoch,
    EpochVectorRejected,
    capture_disconnected_epoch_vector,
    review_disconnected_epoch_progress,
)


def _s(name="memory", gen=1, events=1, time=100, **kw):
    return DisconnectedStoreEpoch(
        store_id=name,
        incarnation_sha256="a" * 64,
        schema_sha256="b" * 64,
        generation=gen,
        event_count=events,
        event_tail_sha256=("c" if events == 1 else "d") * 64,
        state_sha256=("e" if gen == 1 else "f") * 64,
        logical_time_ns=time,
        **kw,
    )


def _v(*stores):
    return capture_disconnected_epoch_vector(tuple(stores))


def test_canonical_repeated_claims_and_no_authority():
    first = _v(_s())
    assert _v(_s()) == first
    assert len(first.digest) == 64
    assert review_disconnected_epoch_progress(first, first) == first
    assert first.coherent_snapshot_proven is False
    assert first.trusted_time_proven is False
    assert first.independent_custody_proven is False
    assert first.memory_disclosure_authorized is False
    assert first.dispatch_authorized is False


def test_multi_store_one_advances_others_stable():
    prev = _v(_s("memory"), _s("planner"))
    current = _v(_s("memory", 2, 2, 101), _s("planner"))
    assert review_disconnected_epoch_progress(prev, current) == current


def test_generation_can_skip_intermediate_versions():
    prev = _v(_s())
    current = _v(_s(gen=20, events=25, time=100))
    assert review_disconnected_epoch_progress(prev, current) == current


@pytest.mark.parametrize("kw", [
    {"gen": 0, "events": 1},
    {"gen": 2, "events": 0},
    {"gen": 2, "events": 1},
    {"gen": 1, "events": 2},
    {"gen": 1, "events": 1, "time": 99},
])
def test_rollback_or_silent_mutation_fails(kw):
    prev = _v(_s())
    with pytest.raises(EpochVectorRejected):
        review_disconnected_epoch_progress(prev, _v(_s(**kw)))


def test_increment_must_change_state_and_tail():
    prev = _v(_s())
    changed = replace(_s(gen=2, events=2), state_sha256="e" * 64)
    with pytest.raises(EpochVectorRejected, match="witness"):
        review_disconnected_epoch_progress(prev, _v(changed))
    changed = replace(_s(gen=2, events=2), event_tail_sha256="c" * 64)
    with pytest.raises(EpochVectorRejected, match="witness"):
        review_disconnected_epoch_progress(prev, _v(changed))


@pytest.mark.parametrize("field", ["store_id", "incarnation_sha256", "schema_sha256"])
def test_identity_or_schema_swap_rejected(field):
    prior = _v(_s())
    replacement = {"store_id": "planner", "incarnation_sha256": "9" * 64,
                   "schema_sha256": "8" * 64}[field]
    observed = _v(replace(_s(), **{field: replacement}))
    with pytest.raises(EpochVectorRejected, match="identity or schema"):
        review_disconnected_epoch_progress(prior, observed)


def test_missing_or_added_store_rejected():
    prior = _v(_s("memory"), _s("planner"))
    with pytest.raises(EpochVectorRejected, match="membership"):
        review_disconnected_epoch_progress(prior, _v(_s("memory")))


def test_ordered_unique_store_names_required():
    for stores in (
        (), (_s("planner"), _s("memory")), (_s("memory"), _s("memory")),
        (_s("Bad-name"),), (_s(""),),
    ):
        with pytest.raises(EpochVectorRejected):
            _v(*stores)


def test_store_count_budget():
    stores = tuple(_s("s" + str(i).zfill(2)) for i in range(17))
    with pytest.raises(EpochVectorRejected):
        _v(*stores)


@pytest.mark.parametrize("value", [
    replace(_s(), generation=True),
    replace(_s(), event_count=-1),
    replace(_s(), logical_time_ns=2**63),
    replace(_s(), event_tail_sha256="z" * 64),
    replace(_s(), incarnation_sha256="c"),
    replace(_s(), state_sha256=None),
    replace(_s(), schema_sha256="A" * 64),
])
def test_exact_field_types_and_sha_required(value):
    with pytest.raises(EpochVectorRejected):
        _v(value)


def test_reject_rewritten_vector_digest():
    original = _v(_s())
    with pytest.raises(EpochVectorRejected, match="digest"):
        review_disconnected_epoch_progress(
            replace(original, digest="0" * 64), original,
        )


def test_reject_other_object_and_forged_vector_tuple():
    v = _v(_s())
    with pytest.raises(EpochVectorRejected, match="exact vector"):
        review_disconnected_epoch_progress({}, v)
    with pytest.raises(EpochVectorRejected):
        review_disconnected_epoch_progress(
            DisconnectedEpochVector(stores=[_s()], digest=v.digest), v,
        )


def test_input_carriers_frozen():
    item = _s()
    with pytest.raises(FrozenInstanceError):
        item.generation = 8


def test_tuple_only_and_exact_dataclass_type():
    with pytest.raises(EpochVectorRejected):
        capture_disconnected_epoch_vector([_s()])
    with pytest.raises(EpochVectorRejected):
        capture_disconnected_epoch_vector((object(),))
