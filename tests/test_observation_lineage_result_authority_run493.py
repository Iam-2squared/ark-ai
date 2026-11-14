"""Detached observation lineage cannot promote review into capture/dispatch authority.

Only synthetic metadata is supplied; no camera, microphone or Tool is opened.
"""

from __future__ import annotations

import pytest

import ark.observation_lineage_review as lineage
from ark.observations import ObservationEnvelope, ObservationKind


def _review():
    envelope = ObservationEnvelope(
        ObservationKind.TEXT, "fixture", "fixture:text", "local:private",
        10, "a" * 64,
    )
    return lineage.review_synthetic_observation_lineage(
        (envelope,), privacy_scope="local:private",
        now_ms=11, max_age_ms=10,
    )


@pytest.mark.parametrize(
    "name",
    ("media_capture_authorized", "disclosure_authorized", "dispatch_authorized"),
)
def test_lineage_result_denies_reflected_authority_properties(monkeypatch, name):
    monkeypatch.setattr(
        lineage.SyntheticObservationLineageWitness,
        name,
        property(lambda self: True),
    )
    with pytest.raises(
        lineage.SyntheticObservationLineageRejected, match="result changed",
    ):
        _review()


def test_unmodified_lineage_result_remains_inert():
    result = _review()
    assert result.media_capture_authorized is False
    assert result.disclosure_authorized is False
    assert result.dispatch_authorized is False
    assert result.observation_count == 1
