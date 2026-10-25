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
    return ObservationEnvelope(
        kind=kind,
        source_id=source_id,
        adapter_id=f"fixture:{kind.value}:v1",
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
    return ObservationEnvelope(
        kind=kind,
        source_id=source_id,
        adapter_id=f"fixture:{kind.value}:v1",
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=digest,
        parent_sha256=parent_sha256,
    )
