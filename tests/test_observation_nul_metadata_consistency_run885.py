"""Direct and synthetic observations share one NUL-free metadata boundary.

In-memory synthetic bytes only. No sensor, filesystem, network or tool use.
"""

import hashlib
import sys

import pytest

from ark import disconnected_observation_fixture as fixture
from ark import observations


def _direct(field: str, value: str) -> observations.ObservationEnvelope:
    fields: dict[str, object] = {
        "kind": observations.ObservationKind.TEXT,
        "source_id": "source",
        "adapter_id": "fixture.disconnected.v1",
        "privacy_scope": "local-private",
        "ingested_at_ms": 0,
        "content_sha256": "a" * 64,
    }
    fields[field] = value
    return observations.ObservationEnvelope(**fields)


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_direct_observation_rejects_embedded_nul(field: str) -> None:
    with pytest.raises(ValueError, match="NUL separator"):
        _direct(field, "trusted\x00untrusted")


@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_disconnected_fixture_rejects_nul_before_private_payload_hash(
    field: str,
) -> None:
    observed: list[object] = []
    previous = sys.getprofile()

    def profile(frame: object, event: str, arg: object) -> None:
        if (
            event == "c_call"
            and getattr(frame, "f_code", None)
            is fixture.make_disconnected_fixture.__code__
            and arg is hashlib.sha256
        ):
            observed.append(arg)

    inputs: dict[str, object] = {
        "kind": observations.ObservationKind.TEXT,
        "source_id": "source",
        "privacy_scope": "private",
        "ingested_at_ms": 1,
        "payload": b"synthetic private bytes",
    }
    inputs[field] = "valid\x00malformed"
    sys.setprofile(profile)
    try:
        with pytest.raises(ValueError, match="NUL separator"):
            fixture.make_disconnected_fixture(**inputs)  # type: ignore[arg-type]
    finally:
        sys.setprofile(previous)
    assert observed == []


@pytest.mark.parametrize("label", ("boundary-safe", "🪐" * 256))
def test_valid_labels_still_support_content_minimized_observation(
    label: str,
) -> None:
    result = fixture.make_disconnected_fixture(
        kind=observations.ObservationKind.TRANSCRIPT,
        source_id=label,
        privacy_scope="private",
        ingested_at_ms=42,
        payload=b"synthetic",
    )
    assert result.source_id == label
    assert len(result.observation_id) == 68
    assert result.content_sha256 == hashlib.sha256(b"synthetic").hexdigest()
    assert not hasattr(result, "payload")
