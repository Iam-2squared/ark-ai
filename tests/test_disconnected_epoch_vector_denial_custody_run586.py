"""Pin false-only epoch-vector descriptors and refuse reflective receipt mutation."""

from __future__ import annotations

import pytest

import ark.disconnected_epoch_vector as epochs


def _claims():
    return (
        epochs.DisconnectedStoreEpoch(
            "memory", "a" * 64, "b" * 64, 1, 1,
            "c" * 64, "d" * 64, 10,
        ),
    )


@pytest.mark.parametrize("name", epochs._DENIAL_NAMES)
def test_equal_false_authority_getter_replacement_is_not_original(
    monkeypatch, name,
):
    monkeypatch.setattr(
        epochs.DisconnectedEpochVector, name, property(lambda _: False),
    )
    with pytest.raises(epochs.EpochVectorRejected, match="acquired authority"):
        epochs.capture_disconnected_epoch_vector(_claims())


@pytest.mark.parametrize("name", epochs._DENIAL_NAMES)
def test_retained_vector_refuses_false_getter_replacement(monkeypatch, name):
    retained = epochs.capture_disconnected_epoch_vector(_claims())
    observed = epochs.capture_disconnected_epoch_vector(_claims())
    monkeypatch.setattr(
        epochs.DisconnectedEpochVector, name, property(lambda _: False),
    )
    with pytest.raises(epochs.EpochVectorRejected, match="acquired authority"):
        epochs.review_disconnected_epoch_progress(retained, observed)


def test_false_getter_cannot_retarget_digest_carrier(monkeypatch):
    original = epochs.DisconnectedEpochVector.__getattribute__

    def mutate(self, name):
        if name == "coherent_snapshot_proven":
            digest = original(self, "digest")
            object.__setattr__(self, "digest", (" " + digest)[1:])
            assert self.digest == digest and self.digest is not digest
            return False
        return original(self, name)

    monkeypatch.setattr(
        epochs.DisconnectedEpochVector, "__getattribute__", mutate,
    )
    with pytest.raises(
        epochs.EpochVectorRejected, match="changed during denial check",
    ):
        epochs.capture_disconnected_epoch_vector(_claims())


def test_false_getter_cannot_replace_later_denial_descriptor(monkeypatch):
    original = epochs.DisconnectedEpochVector.__getattribute__

    def mutate(self, name):
        if name == "coherent_snapshot_proven":
            monkeypatch.setattr(
                epochs.DisconnectedEpochVector,
                "trusted_time_proven", property(lambda _: False),
            )
            return False
        return original(self, name)

    monkeypatch.setattr(
        epochs.DisconnectedEpochVector, "__getattribute__", mutate,
    )
    with pytest.raises(
        epochs.EpochVectorRejected, match="changed during denial check",
    ):
        epochs.capture_disconnected_epoch_vector(_claims())


def test_unmodified_equal_epochs_still_admit_consistency_hint():
    retained = epochs.capture_disconnected_epoch_vector(_claims())
    observed = epochs.capture_disconnected_epoch_vector(_claims())
    assert epochs.review_disconnected_epoch_progress(retained, observed) is observed
    assert observed.dispatch_authorized is False
    assert observed.trusted_time_proven is False
