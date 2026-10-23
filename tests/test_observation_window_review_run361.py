"""Synthetic observation windows: freshness, scope, identity, and zero dispatch."""

import hashlib

import pytest

from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _envelope(source="source", *, scope="fixture:private", at=100, payload=b"data"):
    return ObservationEnvelope(
        ObservationKind.TEXT,
        source,
        "synthetic-adapter",
        scope,
        at,
        hashlib.sha256(payload).hexdigest(),
    )


def _window(*envelopes, scope="fixture:private", now=110, age=20):
    return ObservationWindowReview(scope, now, age, tuple(envelopes))


def test_witness_is_deterministic_and_content_free():
    left = _window(_envelope())
    right = _window(_envelope())
    assert left.witness == right.witness
    assert left.witness.startswith("window_")
    assert len(left.witness) == len("window_") + 64
    assert "data" not in repr(left)


def test_order_and_provenance_affect_window_identity():
    first = _envelope("first")
    second = _envelope("second")
    assert _window(first, second).witness != _window(second, first).witness
    assert _window(first).witness != _window(_envelope("changed-source"))
    assert _window(first, now=111).witness != _window(first, now=110)


@pytest.mark.parametrize(
    "source, now, age",
    [
        (_envelope(scope="other:scope"), 110, 20),
        (_envelope(at=120), 110, 20),
        (_envelope(at=50), 110, 20),
    ],
)
def test_scope_future_and_stale_observations_are_rejected(source, now, age):
    with pytest.raises(ValueError):
        _window(source, now=now, age=age)


def test_boundary_age_is_inclusive():
    assert _window(_envelope(at=90), now=110, age=20).witness.startswith("window_")


def test_duplicate_observation_id_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        _window(_envelope(), _envelope())


def test_invalid_envelope_collections_fail_closed():
    with pytest.raises(ValueError, match="tuple"):
        ObservationWindowReview("fixture:private", 110, 20, [])
    with pytest.raises(ValueError, match="tuple"):
        _window()
    with pytest.raises(ValueError, match="max 256"):
        _window(*(_envelope(str(i)) for i in range(257)))
    with pytest.raises(TypeError, match="exact ObservationEnvelope"):
        _window(object())


def test_reflected_envelope_change_is_detected_on_reuse():
    envelope = _envelope()
    window = _window(envelope)
    old = window.witness
    object.__setattr__(envelope, "content_sha256", "a" * 64)
    with pytest.raises(ValueError, match="identity changed"):
        window.assert_consistent()
    object.__setattr__(envelope, "content_sha256", hashlib.sha256(b"data").hexdigest())
    assert window.witness == old


def test_reflected_tuple_replacement_is_detected_even_if_value_equal():
    window = _window(_envelope())
    object.__setattr__(window, "envelopes", (_envelope(),))
    with pytest.raises(ValueError, match="identity changed"):
        window.assert_consistent()


@pytest.mark.parametrize(
    "scope, now, age",
    [
        ("", 110, 20),
        ("fixture:private", True, 20),
        ("fixture:private", 110, False),
        ("fixture:private", -1, 20),
        ("fixture:private", 110, -1),
    ],
)
def test_invalid_window_header_is_rejected(scope, now, age):
    with pytest.raises(ValueError):
        _window(_envelope(), scope=scope, now=now, age=age)


def test_envelopes_have_no_execution_or_consent_authority():
    window = _window(_envelope())
    for field in ("grant", "authorization", "token", "tool_call", "backend"):
        assert not hasattr(window, field)
    window.assert_consistent()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("privacy_scope", "other:scope"),
        ("observed_at_ms", 120),
        ("max_age_ms", 100),
    ],
)
def test_reflected_header_widening_is_rejected_on_reuse(field, value):
    window = _window(_envelope())
    original_witness = window.witness
    object.__setattr__(window, field, value)
    with pytest.raises(ValueError, match="header changed"):
        window.assert_consistent()
    assert original_witness.startswith("window_")
