"""Run1109: reject invalid Observation fixture metadata before hashing bytes."""

from __future__ import annotations

import pytest

from ark import observation_fixture_adapters as adapters
from ark.observations import ObservationKind


class _StringAlias(str):
    pass


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        pytest.param(
            "source_id", object(), "source_id must be a non-empty exact string",
            id="source-exact-type",
        ),
        pytest.param(
            "source_id", _StringAlias("alias"),
            "source_id must be a non-empty exact string",
            id="source-subclass",
        ),
        pytest.param(
            "source_id", " " * 2, "source_id must be a non-empty exact string",
            id="source-blank",
        ),
        pytest.param(
            "source_id", "x" * 1025, "source_id exceeds observation identifier budget",
            id="source-character-budget",
        ),
        pytest.param(
            "source_id", "synthetic\x00source", "source_id contains a NUL separator",
            id="source-nul",
        ),
        pytest.param(
            "source_id", "synthetic\nsource",
            "source_id contains an ASCII control delimiter",
            id="source-ascii-control",
        ),
        pytest.param(
            "privacy_scope", "private:\u202espoof",
            "privacy_scope contains a Unicode formatting control",
            id="privacy-bidi-control",
        ),
        pytest.param(
            "source_id", "\ud800", "source_id is not valid UTF-8 text",
            id="source-invalid-utf8",
        ),
        pytest.param(
            "ingested_at_ms", True,
            "ingested_at_ms must be a non-negative exact integer",
            id="timestamp-bool",
        ),
        pytest.param(
            "parent_sha256", "A" * 64,
            "parent_sha256 must be an exact lowercase SHA-256 digest",
            id="parent-uppercase-digest",
        ),
    ),
)
@pytest.mark.parametrize("adapter_kind", ("text", "binary"))
def test_invalid_metadata_is_rejected_before_private_sha256(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
    adapter_kind: str,
) -> None:
    metadata: dict[str, object] = {
        "source_id": "synthetic-source",
        "privacy_scope": "private:fixture",
        "ingested_at_ms": 1234,
        "parent_sha256": None,
    }
    metadata[field] = value
    touched: list[bytes] = []

    def forbidden_sha256(payload: bytes):
        touched.append(payload)
        raise AssertionError("invalid metadata reached private SHA-256")

    # If metadata validation were skipped, the fixture hasher would invoke
    # this sentinel. The expected metadata-specific error must happen first.
    with monkeypatch.context() as scoped:
        scoped.setattr(adapters, "_ORIGINAL_SHA256", forbidden_sha256)
        if adapter_kind == "text":
            with pytest.raises(ValueError, match=message):
                adapters.fixture_text_observation(
                    "synthetic-private-text",
                    kind=ObservationKind.TEXT,
                    **metadata,
                )
        else:
            with pytest.raises(ValueError, match=message):
                adapters.fixture_binary_observation(
                    b"synthetic-private-image",
                    kind=ObservationKind.IMAGE,
                    **metadata,
                )

    assert touched == []


@pytest.mark.parametrize("adapter_kind", ("text", "binary"))
def test_rebound_hash_entrypoints_are_rejected_before_receiving_payload(
    monkeypatch: pytest.MonkeyPatch,
    adapter_kind: str,
) -> None:
    touched: list[bytes] = []

    def forbidden_sha256(payload: bytes):
        touched.append(payload)
        raise AssertionError("replacement digest callback received private bytes")

    with monkeypatch.context() as scoped:
        if adapter_kind == "text":
            scoped.setattr(adapters.hashlib, "sha256", forbidden_sha256)
            with pytest.raises(ValueError, match="digest implementation changed"):
                adapters.fixture_text_observation(
                    "synthetic-private-text",
                    kind=ObservationKind.TEXT,
                    source_id="synthetic-source",
                    privacy_scope="private:fixture",
                    ingested_at_ms=1234,
                )
        else:
            scoped.setattr(adapters, "_hash_private_fixture", forbidden_sha256)
            with pytest.raises(ValueError, match="private digest helper changed"):
                adapters.fixture_binary_observation(
                    b"synthetic-private-image",
                    kind=ObservationKind.IMAGE,
                    source_id="synthetic-source",
                    privacy_scope="private:fixture",
                    ingested_at_ms=1234,
                )

    assert touched == []
