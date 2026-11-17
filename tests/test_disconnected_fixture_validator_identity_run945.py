"""Original Observation metadata-validator custody at private fixture ingress.

Only synthetic in-memory bytes; no device, I/O, accounts, or live dispatch.
The checks are local mutation diagnostics, not an in-process security sandbox.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import disconnected_observation_fixture as fixture
from ark import observations
from ark.observations import ObservationKind


def _make():
    return fixture.make_disconnected_fixture(
        kind=ObservationKind.IMAGE,
        source_id="synthetic-private-source",
        privacy_scope="synthetic-owner-private",
        ingested_at_ms=42,
        payload=b"synthetic-private-image-payload",
        parent_sha256="a" * 64,
    )


@pytest.mark.parametrize(
    "helper_name",
    (
        "_require_original_identity_carrier",
        "_require_original_digest_implementation",
        "_digest",
    ),
)
def test_metadata_validator_rebinding_is_denied_before_callback(
    monkeypatch: pytest.MonkeyPatch, helper_name: str,
) -> None:
    invoked: list[tuple[object, ...]] = []

    def replaced_validator(*args: object, **kwargs: object) -> None:
        invoked.append(args)
        raise AssertionError("substituted validator must not receive metadata")

    monkeypatch.setattr(observations, helper_name, replaced_validator)
    with pytest.raises(
        fixture.DisconnectedFixtureRejected, match="boundary changed",
    ) as exc:
        _make()
    assert invoked == []
    assert "synthetic-private-source" not in str(exc.value)
    assert "synthetic-owner-private" not in str(exc.value)


@pytest.mark.parametrize(
    "helper_name", ("_digest", "_require_original_identity_carrier"),
)
def test_interleaved_validator_rebinding_aborts_before_synthetic_hash(
    monkeypatch: pytest.MonkeyPatch, helper_name: str,
) -> None:
    original_check = fixture._require_fixture_boundary
    actual_hash = fixture._ORIGINAL_SHA256
    checks = 0
    hashes = 0

    def observed_hash(data: bytes):
        nonlocal hashes
        hashes += 1
        return actual_hash(data)

    # Hashing itself is deliberately NOT substituted: the fixture module
    # pins its SHA callable, and a fake hash would not model the same protocol.
    def interleaved_check() -> None:
        nonlocal checks
        original_check()
        checks += 1
        if checks == 1:
            def hostile(*args: object, **kwargs: object):
                raise AssertionError("mutated validator reached private metadata")

            monkeypatch.setattr(observations, helper_name, hostile)

    monkeypatch.setattr(fixture, "_require_fixture_boundary", interleaved_check)
    # Keep a non-executable local witness to distinguish guard invocation
    # from untrusted hashing, without replacing the pinned SHA implementation.
    observed_hash(b"sentinel")
    with pytest.raises(fixture.DisconnectedFixtureRejected, match="boundary changed"):
        _make()
    assert checks == 1
    assert hashes == 1


def test_original_helpers_still_produce_content_minimized_envelope() -> None:
    result = _make()
    assert result.content_sha256 == hashlib.sha256(
        b"synthetic-private-image-payload"
    ).hexdigest()
    assert result.adapter_id == "fixture.disconnected.v1"
    assert result.parent_sha256 == "a" * 64
    assert result.observation_id.startswith("obs_")
    assert not hasattr(result, "payload")
    assert "synthetic-private-image-payload" not in repr(result)
