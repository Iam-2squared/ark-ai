"""Cached Observation lineage requires fresh, exact, offline revalidation."""

import hashlib

import pytest

import ark.observation_reuse_review as reuse_module
from ark.observation_lineage_review import review_synthetic_observation_lineage
from ark.observation_reuse_review import (
    SyntheticObservationReuseRejected,
    review_synthetic_observation_reuse,
)
from ark.observations import ObservationEnvelope, ObservationKind


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _envelopes():
    parent = ObservationEnvelope(
        ObservationKind.TEXT, "offline-source", "fixture-a",
        "private-fixture", 100, _hash(b"SECRET-PARENT"),
    )
    child = ObservationEnvelope(
        ObservationKind.TRANSCRIPT, "offline-source", "fixture-b",
        "private-fixture", 105, _hash(b"SECRET-CHILD"),
        parent.content_sha256,
    )
    return (parent, child)


def _cached(envelopes):
    return review_synthetic_observation_lineage(
        envelopes, privacy_scope="private-fixture", now_ms=110,
        max_age_ms=20,
    )


def _reuse(cached, envelopes, **kwargs):
    arguments = dict(
        privacy_scope="private-fixture", now_ms=115,
        max_observation_age_ms=20, max_review_age_ms=10,
    )
    arguments.update(kwargs)
    return review_synthetic_observation_reuse(cached, envelopes, **arguments)


def test_fresh_history_is_locally_rechecked_but_inert():
    envelopes = _envelopes()
    original = _cached(envelopes)
    receipt = _reuse(original, envelopes)
    assert receipt.previous_lineage_digest == original.lineage_digest
    assert receipt.current_lineage_digest != original.lineage_digest
    assert receipt.observation_count == 2
    assert receipt.media_capture_authorized is False
    assert receipt.disclosure_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert "SECRET" not in repr(receipt)


def test_same_time_idempotence():
    envelopes = _envelopes()
    cached = _cached(envelopes)
    receipt = _reuse(cached, envelopes, now_ms=110)
    assert receipt.current_lineage_digest == cached.lineage_digest


@pytest.mark.parametrize("kwargs", [
    {"now_ms": 109},
    {"now_ms": 121, "max_review_age_ms": 10},
    {"now_ms": 115, "max_review_age_ms": 4},
    {"privacy_scope": "wrong"},
])
def test_old_scope_or_stale_cached_review_is_rejected(kwargs):
    envelopes = _envelopes()
    with pytest.raises(SyntheticObservationReuseRejected, match="scope|clock|window"):
        _reuse(_cached(envelopes), envelopes, **kwargs)


def test_oldest_observation_age_is_rechecked_at_use_time():
    envelopes = _envelopes()
    with pytest.raises(ValueError, match="age budget"):
        _reuse(_cached(envelopes), envelopes, now_ms=121, max_review_age_ms=20)


def test_original_lineage_is_rebound_to_original_age_policy():
    envelopes = _envelopes()
    with pytest.raises(SyntheticObservationReuseRejected, match="historical"):
        _reuse(_cached(envelopes), envelopes, max_observation_age_ms=30)


def test_altered_source_identity_rejected_without_content_access():
    envelopes = _envelopes()
    old = _cached(envelopes)
    object.__setattr__(envelopes[0], "adapter_id", "substituted-adapter")
    with pytest.raises(SyntheticObservationReuseRejected, match="historical"):
        _reuse(old, envelopes)


def test_reflected_cached_witness_type_change_rejected():
    envelopes = _envelopes()
    cached = _cached(envelopes)
    object.__setattr__(cached, "observation_count", True)
    with pytest.raises(SyntheticObservationReuseRejected, match="exact"):
        _reuse(cached, envelopes)


def test_reflected_source_after_last_lineage_read_is_rejected(monkeypatch):
    envelopes = _envelopes()
    cached = _cached(envelopes)
    original = reuse_module.review_synthetic_observation_lineage
    count = 0

    def inject(*args, **kwargs):
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == 2:
            object.__setattr__(envelopes[0], "adapter_id", "late-mutation")
        return result

    monkeypatch.setattr(reuse_module, "review_synthetic_observation_lineage", inject)
    with pytest.raises(SyntheticObservationReuseRejected, match="changed"):
        _reuse(cached, envelopes)


def test_reflected_cached_digest_after_last_lineage_read_is_rejected(monkeypatch):
    envelopes = _envelopes()
    cached = _cached(envelopes)
    original = reuse_module.review_synthetic_observation_lineage
    count = 0

    def inject(*args, **kwargs):
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == 2:
            object.__setattr__(cached, "lineage_digest", "forged")
        return result

    monkeypatch.setattr(reuse_module, "review_synthetic_observation_lineage", inject)
    with pytest.raises(SyntheticObservationReuseRejected, match="changed"):
        _reuse(cached, envelopes)


@pytest.mark.parametrize("value", [True, "115", -1, 2**63])
def test_exact_use_time_bounds_required(value):
    envelopes = _envelopes()
    with pytest.raises(SyntheticObservationReuseRejected, match="exact"):
        _reuse(_cached(envelopes), envelopes, now_ms=value)


def test_cached_and_source_container_types_required():
    envelopes = _envelopes()
    cached = _cached(envelopes)
    with pytest.raises(SyntheticObservationReuseRejected, match="exact"):
        _reuse(object(), envelopes)
    with pytest.raises(SyntheticObservationReuseRejected, match="exact"):
        _reuse(cached, list(envelopes))
