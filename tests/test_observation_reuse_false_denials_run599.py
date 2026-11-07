"""Synthetic freshness does not accept altered False-only authority.

No devices, raw media, account, notification, network, or ToolBackend.
"""

import hashlib

import pytest

import ark.observation_reuse_review as reuse
from ark.observation_lineage_review import review_synthetic_observation_lineage
from ark.observations import ObservationEnvelope, ObservationKind


def _inputs():
    original = ObservationEnvelope(
        ObservationKind.TRANSCRIPT, "fixture-text", "fixture-v1",
        "local-private", 100, hashlib.sha256(b"synthetic fixture").hexdigest(),
    )
    envelopes = (original,)
    previous = review_synthetic_observation_lineage(
        envelopes, privacy_scope="local-private",
        now_ms=105, max_age_ms=50,
    )
    return previous, envelopes


def _review(previous, envelopes):
    return reuse.review_synthetic_observation_reuse(
        previous, envelopes, privacy_scope="local-private", now_ms=110,
        max_observation_age_ms=50, max_review_age_ms=10,
    )


@pytest.mark.parametrize("field", (
    "media_capture_authorized", "disclosure_authorized",
    "notification_authorized", "dispatch_authorized",
))
def test_false_looking_reuse_authority_swap_is_rejected(monkeypatch, field):
    inputs = _inputs()
    monkeypatch.setattr(
        reuse.SyntheticObservationReuseReview, field,
        property(lambda _result: False),
    )
    with pytest.raises(
        reuse.SyntheticObservationReuseRejected,
        match="authority descriptor changed",
    ):
        _review(*inputs)


def test_lineage_callback_cannot_install_late_false_denial(monkeypatch):
    inputs = _inputs()
    original_review = reuse.review_synthetic_observation_lineage

    def late_swap(*args, **kwargs):
        result = original_review(*args, **kwargs)
        if kwargs["now_ms"] == 110:
            monkeypatch.setattr(
                reuse.SyntheticObservationReuseReview,
                "notification_authorized", property(lambda _result: False),
            )
        return result

    monkeypatch.setattr(reuse, "review_synthetic_observation_lineage", late_swap)
    with pytest.raises(
        reuse.SyntheticObservationReuseRejected,
        match="authority descriptor changed",
    ):
        _review(*inputs)


def test_original_freshness_receipt_still_has_no_authority():
    result = _review(*_inputs())
    assert result.observation_count == 1
    assert result.checked_at_ms == 110
    assert result.media_capture_authorized is False
    assert result.disclosure_authorized is False
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
