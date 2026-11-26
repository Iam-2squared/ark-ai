"""Bad observation labels must fail before private fixture/lineage access.

Synthetic input only: no device capture, media content, network or backend.
"""

from __future__ import annotations

import pytest

import ark.observation_fixture_adapters as adapters
from ark.observation_fixture_chain_review import (
    ObservationFixtureChainRejected,
    review_disconnected_fixture_chain,
)
from ark.observations import ObservationEnvelope, ObservationKind

_INVALID_LABELS = (
    ("nul", "source\x00trailer"),
    ("surrogate", "source\ud800"),
    ("utf8-budget", "\u754c" * 342),
)


@pytest.mark.parametrize("label_name,bad", _INVALID_LABELS)
@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_requested_chain_label_refused_before_reading_private_envelope(
    field: str, label_name: str, bad: str,
) -> None:
    # This intentionally uninitialized envelope would raise AttributeError
    # if a private slot were accessed before rejecting the requested label.
    unread = object.__new__(ObservationEnvelope)
    arguments = {"source_id": "fixture", "privacy_scope": "synthetic"}
    arguments[field] = bad
    with pytest.raises(ObservationFixtureChainRejected):
        review_disconnected_fixture_chain((unread,), **arguments)


@pytest.mark.parametrize("label_name,bad", _INVALID_LABELS)
@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_binary_fixture_label_refused_before_private_digest_callback(
    monkeypatch: pytest.MonkeyPatch, field: str, label_name: str, bad: str,
) -> None:
    invoked: list[bool] = []

    def forbidden_hash(_payload: bytes) -> str:
        invoked.append(True)
        raise AssertionError("private fixture bytes reached substituted hash")

    monkeypatch.setattr(adapters, "_hash_private_fixture", forbidden_hash)
    arguments = {"source_id": "fixture", "privacy_scope": "synthetic"}
    arguments[field] = bad
    with pytest.raises(ValueError):
        adapters.fixture_binary_observation(
            b"private-synthetic-fixture",
            kind=ObservationKind.IMAGE,
            ingested_at_ms=10,
            **arguments,
        )
    assert not invoked
