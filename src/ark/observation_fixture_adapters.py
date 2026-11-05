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
_ORIGINAL_ENVELOPE_INIT = vars(_ENVELOPE_TYPE)["__init__"]
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
    # An imported constructor symbol can be swapped for an arbitrary callable.
    # Reject it before any forged constructor can run or see fixture metadata.
    if ObservationEnvelope is not _ENVELOPE_TYPE:
        raise ValueError("fixture constructor returned a non-envelope result: class changed")
    # The original dataclass initializer is executable. A forged initializer
    # must not run merely because the imported class symbol is still correct.
    # Hashing the fixture may be reentrant; inspect just before construction.
    if vars(_ENVELOPE_TYPE).get("__init__") is not _ORIGINAL_ENVELOPE_INIT:
        raise ValueError("fixture constructor returned a non-envelope result: init changed")
    envelope = ObservationEnvelope(
        kind=kind,
        source_id=source_id,
        adapter_id=adapter_id,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=content_sha256,
        parent_sha256=parent_sha256,
    )
    if ObservationEnvelope is not _ENVELOPE_TYPE or type(envelope) is not _ENVELOPE_TYPE:
        raise ValueError("fixture constructor returned a non-envelope result")
    if vars(_ENVELOPE_TYPE).get("__init__") is not _ORIGINAL_ENVELOPE_INIT:
        raise ValueError("fixture constructor changed during construction")
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
    if ObservationEnvelope is not _ENVELOPE_TYPE:
        raise ValueError("fixture constructor class changed before validation")
    _VALIDATE_ENVELOPE(envelope)
    # The independent validator invokes local digest/metadata callbacks. Even
    # though this is a frozen carrier, a callback can reflectively replace its
    # fields after the constructor's first identity check. Never return such a
    # mixed-epoch envelope as a valid observation fixture.
    after_validation = (
        envelope.kind, envelope.source_id, envelope.adapter_id,
        envelope.privacy_scope, envelope.ingested_at_ms,
        envelope.content_sha256, envelope.parent_sha256,
        envelope.schema_version,
    )
    if (
        ObservationEnvelope is not _ENVELOPE_TYPE
        or type(envelope) is not _ENVELOPE_TYPE
        or any(now is not old for now, old in zip(
            after_validation, expected, strict=True,
        ))
    ):
        raise ValueError("fixture envelope fields changed during validation")
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
