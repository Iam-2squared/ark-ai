"""Detached store epochs are consistency hints, never executable authority."""

from __future__ import annotations

import pytest

from ark.disconnected_epoch_vector import (
    DisconnectedEpochVector,
    DisconnectedStoreEpoch,
    EpochVectorRejected,
    capture_disconnected_epoch_vector,
    review_disconnected_epoch_progress,
)


def _claims() -> tuple[DisconnectedStoreEpoch, ...]:
    return (
        DisconnectedStoreEpoch(
            "memory", "a" * 64, "b" * 64, 0, 0,
            "c" * 64, "d" * 64, 1,
        ),
    )


@pytest.mark.parametrize(
    "flag",
    (
        "coherent_snapshot_proven",
        "trusted_time_proven",
        "independent_custody_proven",
        "memory_disclosure_authorized",
        "dispatch_authorized",
    ),
)
def test_capture_rejects_reflected_authority_flag(monkeypatch, flag):
    monkeypatch.setattr(
        DisconnectedEpochVector, flag, property(lambda self: True),
    )
    with pytest.raises(EpochVectorRejected, match="acquired authority"):
        capture_disconnected_epoch_vector(_claims())


@pytest.mark.parametrize(
    "flag",
    (
        "coherent_snapshot_proven",
        "trusted_time_proven",
        "independent_custody_proven",
        "memory_disclosure_authorized",
        "dispatch_authorized",
    ),
)
def test_review_rejects_reflected_authority_flag(monkeypatch, flag):
    retained = capture_disconnected_epoch_vector(_claims())
    observed = capture_disconnected_epoch_vector(_claims())
    monkeypatch.setattr(
        DisconnectedEpochVector, flag, property(lambda self: True),
    )
    with pytest.raises(EpochVectorRejected, match="acquired authority"):
        review_disconnected_epoch_progress(retained, observed)


def test_same_epoch_is_diagnostic_only():
    retained = capture_disconnected_epoch_vector(_claims())
    observed = capture_disconnected_epoch_vector(_claims())
    assert review_disconnected_epoch_progress(retained, observed) is observed
    assert observed.coherent_snapshot_proven is False
    assert observed.trusted_time_proven is False
    assert observed.independent_custody_proven is False
    assert observed.memory_disclosure_authorized is False
    assert observed.dispatch_authorized is False
