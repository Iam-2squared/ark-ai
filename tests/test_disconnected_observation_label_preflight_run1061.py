"""Oversized disconnected observation labels fail before control scans."""

from __future__ import annotations

import pytest

from ark import disconnected_observation_fixture as fixture
from ark.observations import ObservationKind


@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
@pytest.mark.parametrize("label", ("x" * 100_000, "🪐" * 257))
def test_oversized_label_fails_before_control_scan(
    monkeypatch: pytest.MonkeyPatch, field: str, label: str,
) -> None:
    def forbidden(*_args: object) -> bool:
        raise AssertionError("oversized label reached a control scan")

    monkeypatch.setattr(fixture, "any", forbidden, raising=False)
    values: dict[str, object] = {
        "kind": ObservationKind.TEXT,
        "source_id": "synthetic-source",
        "privacy_scope": "private-synthetic",
        "ingested_at_ms": 123,
        "payload": b"synthetic-payload-only",
    }
    values[field] = label
    with pytest.raises(
        fixture.DisconnectedFixtureRejected,
        match="observation identifier budget",
    ):
        fixture.make_disconnected_fixture(**values)  # type: ignore[arg-type]


def test_exact_1024_byte_multilingual_label_remains_accepted() -> None:
    label = "🪐" * 256
    envelope = fixture.make_disconnected_fixture(
        kind=ObservationKind.TEXT,
        source_id=label,
        privacy_scope="private-synthetic",
        ingested_at_ms=123,
        payload=b"synthetic-payload-only",
    )
    assert envelope.source_id == label
    assert envelope.content_sha256
    assert not hasattr(envelope, "payload")
