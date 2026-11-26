"""Observation lineage denial getters cannot release a changed source/result."""

import pytest

from ark.observation_fixture_adapters import fixture_text_observation
from ark.observation_lineage_review import (
    SyntheticObservationLineageRejected,
    SyntheticObservationLineageWitness,
    review_synthetic_observation_lineage,
)
from ark.observations import ObservationKind


def _envelope():
    return fixture_text_observation(
        "caller-supplied transcript fixture",
        kind=ObservationKind.TEXT,
        source_id="local-fixture",
        privacy_scope="private",
        ingested_at_ms=1000,
    )


def _review(envelope):
    return review_synthetic_observation_lineage(
        (envelope,), privacy_scope="private", now_ms=1200, max_age_ms=1000,
    )


def test_unmodified_lineage_witness_is_inert_and_repeatable():
    envelope = _envelope()
    first = _review(envelope)
    assert first == _review(envelope)
    assert first.lineage_digest.startswith("olineage_")
    assert first.media_capture_authorized is False
    assert first.disclosure_authorized is False
    assert first.dispatch_authorized is False


@pytest.mark.parametrize(
    ("flag", "changed_field", "value"),
    [
        ("media_capture_authorized", "observation_count", 999),
        ("disclosure_authorized", "lineage_digest", "olineage_" + "0" * 64),
        ("dispatch_authorized", "privacy_scope", "public"),
    ],
)
def test_false_authority_getter_rewriting_witness_is_rejected(
    monkeypatch, flag, changed_field, value,
):
    envelope = _envelope()

    def reflected_rewrite(self):
        object.__setattr__(self, changed_field, value)
        return False

    monkeypatch.setattr(
        SyntheticObservationLineageWitness,
        flag,
        property(reflected_rewrite),
    )
    with pytest.raises(SyntheticObservationLineageRejected, match="changed"):
        _review(envelope)


def test_false_authority_getter_rewriting_input_is_rejected(monkeypatch):
    envelope = _envelope()

    def reflected_rewrite(self):
        object.__setattr__(envelope, "privacy_scope", "public")
        return False

    monkeypatch.setattr(
        SyntheticObservationLineageWitness,
        "dispatch_authorized",
        property(reflected_rewrite),
    )
    with pytest.raises(SyntheticObservationLineageRejected, match="changed"):
        _review(envelope)
