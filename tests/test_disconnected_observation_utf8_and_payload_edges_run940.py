"""Exact UTF-8 label and payload-size edges in an inert Observation adapter.

All content is synthetic, in-memory fixture data. No capture, consent, sensor,
user data, device operation, network call or external execution takes place.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.disconnected_observation_fixture import (
    make_disconnected_fixture,
)
from ark.observations import ObservationKind


@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
@pytest.mark.parametrize(
    ("label", "accepted"),
    (
        ("🪐" * 256, True),    # 256 x four-byte UTF-8 == 1024 bytes
        ("🪐" * 257, False),   # 1028 bytes, even though under 1024 chars
        ("a" * 1024, True),   # exact ASCII byte and code-point boundary
        ("a" * 1025, False),
    ),
)
def test_fixture_identifier_byte_budget_at_exact_boundary(
    field: str, label: str, accepted: bool,
) -> None:
    kwargs = {
        "kind": ObservationKind.TEXT,
        "source_id": "synthetic-source",
        "privacy_scope": "synthetic-private",
        "ingested_at_ms": 123,
        "payload": b"synthetic-payload-not-user-data",
    }
    kwargs[field] = label
    if not accepted:
        with pytest.raises(ValueError):
            make_disconnected_fixture(**kwargs)
        return

    result = make_disconnected_fixture(**kwargs)
    assert result.content_sha256 == hashlib.sha256(kwargs["payload"]).hexdigest()
    assert result.observation_id.startswith("obs_")
    assert len(result.observation_id) == 68
    assert not hasattr(result, "payload")
    assert result.schema_version == 1


@pytest.mark.parametrize("kind", tuple(ObservationKind))
def test_maximum_fixture_payload_is_hashed_but_never_retained(kind):
    # The adapter explicitly allows 65,536 exact bytes, but no larger
    # buffer, while keeping raw content out of the returned envelope.
    payload = b"x" * 65_536
    kwargs = {
        "kind": kind,
        "source_id": "synthetic-source",
        "privacy_scope": "synthetic-private",
        "ingested_at_ms": 123,
    }
    envelope = make_disconnected_fixture(**kwargs, payload=payload)
    assert envelope.content_sha256 == hashlib.sha256(payload).hexdigest()
    assert envelope.observation_id.startswith("obs_")
    assert not hasattr(envelope, "payload")
    assert len(repr(envelope)) < 1000

    with pytest.raises(ValueError):
        make_disconnected_fixture(**kwargs, payload=payload + b"x")
