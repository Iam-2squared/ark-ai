"""Late denial callbacks cannot upgrade offline observation lineage authority.

Only synthetic metadata fixtures; no microphone, camera, network or ToolBackend.
"""

import hashlib

import pytest

from ark.observation_lineage_review import (
    SyntheticObservationLineageRejected,
    SyntheticObservationLineageWitness,
    review_synthetic_observation_lineage,
)
from ark.observations import ObservationEnvelope, ObservationKind


def _envelopes():
    return (
        ObservationEnvelope(
            ObservationKind.TEXT,
            "source-fixture",
            "adapter-fixture",
            "local-private-fixture",
            100,
            hashlib.sha256(b"offline fixture").hexdigest(),
        ),
    )


def _review(envelopes):
    return review_synthetic_observation_lineage(
        envelopes, privacy_scope="local-private-fixture",
        now_ms=110, max_age_ms=20,
    )


@pytest.mark.parametrize("target", (
    "media_capture_authorized", "disclosure_authorized",
))
def test_last_false_denial_cannot_replace_earlier_authority(
    monkeypatch, target,
):
    envelopes = _envelopes()

    def late_denial(self):
        monkeypatch.setattr(
            SyntheticObservationLineageWitness,
            target,
            property(lambda self: True),
        )
        return False

    monkeypatch.setattr(
        SyntheticObservationLineageWitness,
        "dispatch_authorized",
        property(late_denial),
    )
    with pytest.raises(SyntheticObservationLineageRejected, match="authority"):
        _review(envelopes)


def test_false_disclosure_cannot_replace_media_denial(monkeypatch):
    envelopes = _envelopes()

    def late_disclosure(self):
        monkeypatch.setattr(
            SyntheticObservationLineageWitness,
            "media_capture_authorized",
            property(lambda self: True),
        )
        return False

    monkeypatch.setattr(
        SyntheticObservationLineageWitness,
        "disclosure_authorized",
        property(late_disclosure),
    )
    with pytest.raises(SyntheticObservationLineageRejected, match="authority"):
        _review(envelopes)


def test_second_denial_pass_rechecks_original_source(monkeypatch):
    envelopes = _envelopes()
    calls = [0]

    def last_denial(self):
        calls[0] += 1
        if calls[0] == 2:
            object.__setattr__(envelopes[0], "source_id", "altered-fixture")
        return False

    monkeypatch.setattr(
        SyntheticObservationLineageWitness,
        "dispatch_authorized",
        property(last_denial),
    )
    # An unreviewed False-only class property is refused before invocation.
    with pytest.raises(SyntheticObservationLineageRejected, match="authority"):
        _review(envelopes)
    assert calls[0] == 0


def test_second_denial_pass_rechecks_result_digest(monkeypatch):
    envelopes = _envelopes()
    calls = [0]

    def last_denial(self):
        calls[0] += 1
        if calls[0] == 2:
            object.__setattr__(self, "lineage_digest", "olineage_" + "f" * 64)
        return False

    monkeypatch.setattr(
        SyntheticObservationLineageWitness,
        "dispatch_authorized",
        property(last_denial),
    )
    with pytest.raises(SyntheticObservationLineageRejected, match="authority"):
        _review(envelopes)
    assert calls[0] == 0


def test_clean_lineage_is_still_diagnostic_only():
    result = _review(_envelopes())
    assert result.observation_count == 1
    assert result.lineage_digest.startswith("olineage_")
    assert result.media_capture_authorized is False
    assert result.disclosure_authorized is False
    assert result.dispatch_authorized is False
