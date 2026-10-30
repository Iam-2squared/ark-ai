"""Explicit, disconnected in-memory observation fixture adapters.

No file, camera, microphone, network, notification or ToolBackend access.
Raw caller-supplied fixture bytes are hashed and never placed in the returned
envelope. These deterministic witnesses do not prove source authenticity,
consent or permission to execute an action.
"""

from __future__ import annotations

import hashlib

from .observations import ObservationEnvelope, ObservationKind

_MAX_FIXTURE_BYTES = 4 * 1024 * 1024
_ENVELOPE_TYPE = ObservationEnvelope
# Keep a stable copy of the frozen v1 validator. An injected constructor or
# __post_init__ replacement must not turn invalid fixture metadata into a
# seemingly valid envelope by skipping the original validation hook.
_VALIDATE_ENVELOPE = ObservationEnvelope.__post_init__


def _sealed_fixture(
    *,
    kind: ObservationKind,
    source_id: str,
    privacy_scope: str,
    ingested_at_ms: int,
    content_sha256: str,
    parent_sha256: str | None,
) -> ObservationEnvelope:
    """Reject a constructor that returns a retargeted or forged fixture.

    Frozen dataclasses can still be changed with object.__setattr__. A fixture
    constructor (including its validation hook) is an untrusted callback and
    cannot silently replace the source, privacy or content identity after the
    caller's raw content was hashed.
    """
    adapter_id = f"fixture:{kind.value}:v1"
    expected = (
        kind, source_id, adapter_id, privacy_scope, ingested_at_ms,
        content_sha256, parent_sha256, 1,
    )
    envelope = ObservationEnvelope(
        kind=kind,
        source_id=source_id,
        adapter_id=adapter_id,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=content_sha256,
        parent_sha256=parent_sha256,
    )
    if type(envelope) is not _ENVELOPE_TYPE:
        raise ValueError("fixture constructor returned a non-envelope result")
    actual = (
        envelope.kind, envelope.source_id, envelope.adapter_id,
        envelope.privacy_scope, envelope.ingested_at_ms,
        envelope.content_sha256, envelope.parent_sha256,
        envelope.schema_version,
    )
    if any(now is not before for now, before in zip(
        actual, expected, strict=True,
    )):
        raise ValueError("fixture envelope fields changed during construction")
    # Preserve legacy retargeting diagnostics before independently rejecting
    # invalid-but-unchanged metadata from a bypassed constructor validator.
    _VALIDATE_ENVELOPE(envelope)
    return envelope


def fixture_text_observation(
    content: str,
    *,
    kind: ObservationKind,
    source_id: str,
    privacy_scope: str,
    ingested_at_ms: int,
    parent_sha256: str | None = None,
) -> ObservationEnvelope:
    """Adapt provided text/transcript in memory; never acquire or retain it."""
    if type(kind) is not ObservationKind or kind not in (
        ObservationKind.TEXT,
        ObservationKind.TRANSCRIPT,
    ):
        raise ValueError("fixture text kind must be exact TEXT or TRANSCRIPT")
    if type(content) is not str:
        raise TypeError("fixture text must be an exact string")
    if len(content) > _MAX_FIXTURE_BYTES:
        raise ValueError("fixture content byte budget exceeded")
    try:
        data = content.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("fixture text is not valid UTF-8") from exc
    if len(data) > _MAX_FIXTURE_BYTES:
        raise ValueError("fixture content byte budget exceeded")
    digest = hashlib.sha256(data).hexdigest()
    return _sealed_fixture(
        kind=kind,
        source_id=source_id,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=digest,
        parent_sha256=parent_sha256,
    )


def fixture_binary_observation(
    payload: bytes,
    *,
    kind: ObservationKind,
    source_id: str,
    privacy_scope: str,
    ingested_at_ms: int,
    parent_sha256: str | None = None,
) -> ObservationEnvelope:
    """Adapt supplied image/screen fixture bytes, without reading a device."""
    if type(kind) is not ObservationKind or kind not in (
        ObservationKind.IMAGE,
        ObservationKind.SCREEN,
    ):
        raise ValueError("fixture binary kind must be exact IMAGE or SCREEN")
    if type(payload) is not bytes:
        raise TypeError("fixture binary payload must be exact bytes")
    if len(payload) > _MAX_FIXTURE_BYTES:
        raise ValueError("fixture content byte budget exceeded")
    digest = hashlib.sha256(payload).hexdigest()
    return _sealed_fixture(
        kind=kind,
        source_id=source_id,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=digest,
        parent_sha256=parent_sha256,
    )
