"""Original observation field carriers remain bound in cached windows.

All inputs are disconnected metadata-only synthetic fixtures. No sensing,
notifications, consent, authentication, or executable ToolBackend is involved.
"""

import pytest

from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _window():
    scope = "local:window-carrier-custody"
    item = ObservationEnvelope(
        ObservationKind.TEXT,
        "long-synthetic-source-identity",
        "fixture:long-adapter-identity:v1",
        scope,
        10_000,
        "a" * 64,
        "b" * 64,
    )
    return ObservationWindowReview(scope, 10_010, 100, (item,)), item


def _equal_distinct(value):
    if type(value) is int:
        result = int(str(value))
    else:
        result = value.encode("utf-8").decode("utf-8")
    assert result == value
    assert result is not value
    return result


@pytest.mark.parametrize(
    "field",
    (
        "source_id", "adapter_id", "privacy_scope", "ingested_at_ms",
        "content_sha256", "parent_sha256",
    ),
)
@pytest.mark.parametrize("entrypoint", ("assert_consistent", "assert_fresh_at", "witness"))
def test_equal_value_field_replacement_cannot_reuse_original_window(
    field, entrypoint,
):
    window, envelope = _window()
    original_witness = window.witness
    original = getattr(envelope, field)
    object.__setattr__(envelope, field, _equal_distinct(original))
    with pytest.raises(ValueError, match="observation identity changed"):
        if entrypoint == "assert_consistent":
            window.assert_consistent()
        elif entrypoint == "assert_fresh_at":
            window.assert_fresh_at(10_011)
        else:
            _ = window.witness
    # Unchanged canonical values still hash to the old identity. Rejecting
    # this review therefore checks original carrier custody, not hash drift.
    assert envelope.observation_id == window._epoch[0][1]
    assert original_witness.startswith("window_")


def test_equal_value_retarget_during_identity_check_is_rejected(monkeypatch):
    window, envelope = _window()
    original = ObservationWindowReview._check_envelope
    calls = []

    def substituted(self, candidate):
        identity = original(self, candidate)
        if not calls:
            object.__setattr__(
                envelope, "source_id", _equal_distinct(envelope.source_id)
            )
            calls.append(True)
        return identity

    monkeypatch.setattr(ObservationWindowReview, "_check_envelope", substituted)
    with pytest.raises(ValueError, match="observation identity changed"):
        window.assert_consistent()
    assert calls == [True]


def test_initial_hydration_rejects_equal_value_field_substitution(monkeypatch):
    original = ObservationWindowReview._check_envelope
    calls = []

    def substituted(self, candidate):
        identity = original(self, candidate)
        if not calls:
            object.__setattr__(
                candidate, "source_id", _equal_distinct(candidate.source_id)
            )
            calls.append(True)
        return identity

    monkeypatch.setattr(ObservationWindowReview, "_check_envelope", substituted)
    with pytest.raises(ValueError, match="identity changed during hydration"):
        _window()
    assert calls == [True]


def test_unchanged_window_witness_remains_deterministic_and_inert():
    window, _ = _window()
    before = window.witness
    window.assert_consistent()
    window.assert_fresh_at(10_015)
    assert window.witness == before
    assert before.startswith("window_")
    for name in ("authorization", "dispatch", "backend", "raw_media"):
        assert not hasattr(window, name)
