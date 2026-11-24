"""Run1178: complete Unicode Cf rejection at privacy metadata boundaries."""

from __future__ import annotations

import pytest

from ark import observation_fixture_adapters as observation_adapters
from ark import personal_context_review, proactive_state_ledger
from ark.observations import ObservationKind

# These are Cf characters outside the older hand-maintained rejection list:
# Arabic Number Sign, Interlinear Annotation Anchor, and Language Tag.
_FORMAT_CONTROLS = ("\u0600", "\ufff9", "\U000e0001")


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
def test_personal_context_policy_rejects_every_unicode_cf(control: str) -> None:
    with pytest.raises(ValueError, match="Unicode formatting control"):
        personal_context_review.ContextSelectionPolicy(
            total_limit=1,
            per_namespace_limit=1,
            policy_revision=f"revision{control}",
        )


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize(
    "field", ("owner", "namespace", "definition_id", "policy_revision"),
)
def test_proactive_policy_rejects_every_unicode_cf(
    control: str, field: str,
) -> None:
    values = {
        "owner": "local-owner",
        "namespace": "private",
        "definition_id": "daily-summary",
        "revision": 1,
        "policy_revision": "policy-v1",
        "minimum_interval_ms": 0,
        "cooldown_ms": 0,
        "rolling_window_ms": 1,
        "max_previews_per_window": 1,
    }
    values[field] += control
    with pytest.raises(
        proactive_state_ledger.SyntheticProactiveStateRejected,
        match="Unicode formatting control",
    ):
        proactive_state_ledger.SyntheticProactivePolicy(**values)


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_observation_fixture_rejects_every_unicode_cf_before_private_hash(
    control: str, field: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched: list[bytes] = []

    def forbidden_hash(payload: bytes) -> str:
        touched.append(payload)
        raise AssertionError("format-controlled fixture reached private hashing")

    monkeypatch.setattr(
        observation_adapters, "_hash_private_fixture", forbidden_hash,
    )
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


def test_personal_context_pins_unicode_category_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        personal_context_review.unicodedata, "category",
        lambda _character: "Lo",
    )
    with pytest.raises(ValueError, match="category classifier changed"):
        personal_context_review.ContextSelectionPolicy(1, 1, "policy-v1")


def test_proactive_state_pins_unicode_category_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        proactive_state_ledger.unicodedata, "category",
        lambda _character: "Lo",
    )
    with pytest.raises(
        proactive_state_ledger.SyntheticProactiveStateRejected,
        match="protocol changed",
    ):
        proactive_state_ledger.SyntheticProactivePolicy(
            "owner", "private", "daily", 1, "policy-v1", 0, 0, 1, 1,
        )


def test_observation_fixture_pins_unicode_category_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        observation_adapters.unicodedata, "category",
        lambda _character: "Lo",
    )
    with pytest.raises(ValueError, match="category classifier changed"):
        observation_adapters.fixture_text_observation(
            "synthetic private fixture",
            kind=ObservationKind.TEXT,
            source_id="synthetic-source",
            privacy_scope="private:fixture",
            ingested_at_ms=1234,
        )
