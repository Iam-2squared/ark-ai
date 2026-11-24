"""Run1234: complete Unicode Cf admission in privacy metadata boundaries."""

from __future__ import annotations

import pytest

from ark import observation_fixture_adapters as observation_adapters
from ark import personal_context_review
from ark.observations import ObservationKind

_FORMAT_CONTROLS = ("\u0600", "\ufff9", "\U000e0001")


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
def test_personal_context_policy_rejects_every_unicode_cf(control: str) -> None:
    with pytest.raises(ValueError, match="Unicode formatting control"):
        personal_context_review.ContextSelectionPolicy(
            total_limit=1,
            per_namespace_limit=1,
            policy_revision=f"revision{control}",
        )


def test_japanese_personal_context_policy_revision_remains_supported() -> None:
    policy = personal_context_review.ContextSelectionPolicy(1, 1, "方針-v1")
    assert policy.policy_revision == "方針-v1"


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_observation_fixture_rejects_every_unicode_cf_before_private_hash(
    control: str,
    field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched: list[bytes] = []

    def forbidden_hash(payload: bytes) -> str:
        touched.append(payload)
        raise AssertionError("format-controlled fixture reached private hashing")

    monkeypatch.setattr(observation_adapters, "_hash_private_fixture", forbidden_hash)
    metadata = {
        "source_id": "synthetic-source",
        "privacy_scope": "private:fixture",
    }
    metadata[field] += control
    with pytest.raises(ValueError, match="Unicode formatting control"):
        observation_adapters.fixture_text_observation(
            "synthetic private fixture",
            kind=ObservationKind.TEXT,
            ingested_at_ms=1234,
            **metadata,
        )
    assert touched == []


def test_japanese_observation_fixture_metadata_remains_supported() -> None:
    envelope = observation_adapters.fixture_text_observation(
        "synthetic private fixture",
        kind=ObservationKind.TEXT,
        source_id="合成ソース",
        privacy_scope="個人:fixture",
        ingested_at_ms=1234,
    )
    assert envelope.source_id == "合成ソース"
    assert envelope.privacy_scope == "個人:fixture"


def test_personal_context_pins_unicode_category_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = personal_context_review.ContextSelectionPolicy(1, 1, "policy-v1")
    calls: list[str] = []

    def forbidden_category(character: str) -> str:
        calls.append(character)
        return "Lo"

    monkeypatch.setattr(personal_context_review.unicodedata, "category", forbidden_category)
    with pytest.raises(ValueError, match="category classifier changed"):
        policy.__post_init__()
    assert calls == []


def test_observation_fixture_pins_unicode_category_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def forbidden_category(character: str) -> str:
        calls.append(character)
        return "Lo"

    monkeypatch.setattr(observation_adapters.unicodedata, "category", forbidden_category)
    with pytest.raises(ValueError, match="category classifier changed"):
        observation_adapters.fixture_text_observation(
            "synthetic private fixture",
            kind=ObservationKind.TEXT,
            source_id="synthetic-source",
            privacy_scope="private:fixture",
            ingested_at_ms=1234,
        )
    assert calls == []
