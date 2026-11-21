"""Run957: source binding uses envelope-equivalent UTF-8 byte admission.

All identities are synthetic. The local source digest is neither capture
provenance nor notification, privacy consent or tool execution authority.
"""

from __future__ import annotations

import pytest

import ark.proactive_observation_lineage_fence_review as trigger
from ark.observations import ObservationEnvelope, ObservationKind


@pytest.mark.parametrize("source", ("a" * 1024, "é" * 512, "🪐" * 256))
def test_bounded_utf8_source_matches_frozen_envelope_admission(source: str) -> None:
    envelope = ObservationEnvelope(
        ObservationKind.TEXT, source, "fixture:text", "private", 42, "a" * 64,
    )
    assert len(source.encode("utf-8")) == 1024
    assert envelope.source_id == source
    digest = trigger.synthetic_observation_source_digest(source)
    assert digest == trigger.synthetic_observation_source_digest(envelope.source_id)
    assert len(digest) == 64


@pytest.mark.parametrize(
    "source",
    ("a" * 1025, "é" * 513, "🪐" * 257, "界" * 342),
)
def test_overbudget_utf8_source_refused_before_private_source_hash(
    source: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert len(source.encode("utf-8")) > 1024
    called = []

    def forbidden_hash(*_args: object) -> str:
        called.append(True)
        pytest.fail("overbudget private source reached digest implementation")

    monkeypatch.setattr(trigger, "_hash", forbidden_hash)
    with pytest.raises(trigger.SyntheticObservationTriggerRejected, match="bounded"):
        trigger.synthetic_observation_source_digest(source)
    assert called == []


@pytest.mark.parametrize("source", ("bad\ud800", "bad\udfff"))
def test_invalid_unicode_refused_before_source_hash(
    source: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = []

    def forbidden_hash(*_args: object) -> str:
        called.append(True)
        pytest.fail("malformed private source reached digest implementation")

    monkeypatch.setattr(trigger, "_hash", forbidden_hash)
    with pytest.raises(trigger.SyntheticObservationTriggerRejected, match="UTF-8"):
        trigger.synthetic_observation_source_digest(source)
    assert called == []


@pytest.mark.parametrize("source", (None, b"bytes", "", "   ", True))
def test_non_text_or_blank_source_does_not_reach_digest(
    source: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = []

    def forbidden_hash(*_args: object) -> str:
        called.append(True)
        pytest.fail("invalid private source reached digest implementation")

    monkeypatch.setattr(trigger, "_hash", forbidden_hash)
    with pytest.raises(trigger.SyntheticObservationTriggerRejected, match="bounded"):
        trigger.synthetic_observation_source_digest(source)  # type: ignore[arg-type]
    assert called == []
