"""Deny same-valued carrier replacement during detached Memory epoch reviews."""

from dataclasses import replace

import pytest

from ark import disconnected_epoch_vector as module
from ark.disconnected_epoch_vector import (
    DisconnectedStoreEpoch,
    EpochVectorRejected,
    capture_disconnected_epoch_vector,
    review_disconnected_epoch_progress,
)


def epoch(version=1, tail="b", state="c"):
    return DisconnectedStoreEpoch(
        "memory", "0" * 64, "1" * 64, version, version, tail * 64,
        state * 64, version * 100,
    )


def capture(store):
    return capture_disconnected_epoch_vector((store,))


def test_valid_progress_and_denied_authority_unchanged():
    prior = capture(epoch())
    later = capture(epoch(2, tail="d", state="e"))
    assert review_disconnected_epoch_progress(prior, later) is later
    assert later.coherent_snapshot_proven is False
    assert later.independent_custody_proven is False
    assert later.dispatch_authorized is False
    assert later.memory_disclosure_authorized is False
    assert capture(epoch()) == prior


def test_same_text_field_replacement_during_capture_rejected(monkeypatch):
    store = epoch()
    original = module._canonical_digest

    def substitute(rows):
        current = store.event_tail_sha256
        replacement = current.encode("ascii").decode("ascii")
        assert replacement == current and replacement is not current
        object.__setattr__(store, "event_tail_sha256", replacement)
        return original(rows)

    monkeypatch.setattr(module, "_canonical_digest", substitute)
    with pytest.raises(EpochVectorRejected, match="carrier"):
        capture(store)


def test_same_text_field_replacement_during_retained_validation_rejected(monkeypatch):
    store = epoch()
    vector = capture(store)
    original = module._canonical_digest

    def substitute(rows):
        current = store.state_sha256
        replacement = current.encode("ascii").decode("ascii")
        object.__setattr__(store, "state_sha256", replacement)
        return original(rows)

    monkeypatch.setattr(module, "_canonical_digest", substitute)
    with pytest.raises(EpochVectorRejected, match="carrier"):
        review_disconnected_epoch_progress(vector, vector)


def test_store_tuple_replacement_with_equal_value_denied(monkeypatch):
    vector = capture(epoch())
    original = module._canonical_digest

    def substitute(rows):
        object.__setattr__(vector, "stores", tuple([vector.stores[0]]))
        return original(rows)

    monkeypatch.setattr(module, "_canonical_digest", substitute)
    with pytest.raises(EpochVectorRejected, match="carrier"):
        review_disconnected_epoch_progress(vector, vector)


def test_constructed_vector_with_replaced_digest_refused(monkeypatch):
    store = epoch()
    original = module.DisconnectedEpochVector

    def substitute(*args, **kw):
        result = original(*args, **kw)
        original_digest = result.digest
        object.__setattr__(result, "digest", original_digest.encode().decode())
        return result

    monkeypatch.setattr(module, "DisconnectedEpochVector", substitute)
    with pytest.raises(EpochVectorRejected, match="constructed"):
        capture(store)


def test_capture_rejects_invalid_carrier_shape_before_field_inspection():
    with pytest.raises(EpochVectorRejected):
        capture_disconnected_epoch_vector((object(),))
    with pytest.raises(EpochVectorRejected):
        capture_disconnected_epoch_vector([epoch()])
    with pytest.raises(EpochVectorRejected):
        capture_disconnected_epoch_vector(())


def test_revision_rollback_remains_denied():
    high = capture(epoch(3))
    low = capture(epoch())
    with pytest.raises(EpochVectorRejected, match="regressed"):
        review_disconnected_epoch_progress(high, low)


@pytest.mark.parametrize("changes", [
    {"generation": True},
    {"event_count": -1},
    {"event_tail_sha256": None},
    {"logical_time_ns": 2**63},
])
def test_invalid_persisted_epoch_claims_still_rejected(changes):
    with pytest.raises(EpochVectorRejected):
        capture(replace(epoch(), **changes))
