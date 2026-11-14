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
# Keep the raw fixture hashing entrypoint fixed at import time. A replaced
# sha256 function could receive caller-private bytes before an envelope is
# even constructed, despite all later constructor/validator custody checks.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ENVELOPE_TYPE = ObservationEnvelope
_ORIGINAL_ENVELOPE_INIT = vars(_ENVELOPE_TYPE)["__init__"]
# Keep a stable copy of the frozen v1 validator. An injected constructor or
# __post_init__ replacement must not turn invalid fixture metadata into a
# seemingly valid envelope by skipping the original validation hook.
_VALIDATE_ENVELOPE = ObservationEnvelope.__post_init__
# Keep the class's original validation identity separate from the intentionally
# substitutable, independent post-construction validation hook exercised by
# offline failure-injection tests.
_ORIGINAL_ENVELOPE_VALIDATOR = _VALIDATE_ENVELOPE
# The imported envelope's frozen dataclass fields, validation callback and
# inherited lookup machinery remain reflectively patchable. Guard their
# import-time identities before constructing any private observation and
# again across validation, not only the direct initializer.
_ENVELOPE_FIELDS = (
    "kind", "source_id", "adapter_id", "privacy_scope", "ingested_at_ms",
    "content_sha256", "parent_sha256", "schema_version",
)
_ENVELOPE_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_ENVELOPE_FIELDS = tuple(
    vars(_ENVELOPE_TYPE)[name] for name in _ENVELOPE_FIELDS
)
_ORIGINAL_ENVELOPE_HOOKS = tuple(
    vars(_ENVELOPE_TYPE).get(name) for name in _ENVELOPE_HOOKS
)


# Fixture sizes are a reviewed ingress contract. Mutating the process-global
# limit must not allow a larger private payload to reach SHA-256 or a fixture
# envelope. This does not authenticate a real camera/microphone source.
_ORIGINAL_MAX_FIXTURE_BYTES = _MAX_FIXTURE_BYTES


def _require_original_fixture_budget() -> None:
    if (
        type(_MAX_FIXTURE_BYTES) is not int
        or _MAX_FIXTURE_BYTES is not _ORIGINAL_MAX_FIXTURE_BYTES
    ):
        raise ValueError("fixture byte budget definition changed")


def _preflight_fixture_metadata(
    source_id: str,
    privacy_scope: str,
    ingested_at_ms: int,
    parent_sha256: str | None,
) -> None:
    """Reject malformed labels before hashing caller-private fixture content.

    This is an input budget/shape check only, not source provenance or consent.
    The envelope independently validates the same values after construction.
    """
    _require_original_fixture_budget()
    for name, value in (
        ("source_id", source_id),
        ("privacy_scope", privacy_scope),
    ):
        if type(value) is not str or not value.strip():
            raise ValueError(f"{name} must be a non-empty exact string")
        # NUL in source/privacy labels is ambiguous at native adapter
        # boundaries. Reject before even hashing caller-private fixture bytes.
        if "\x00" in value:
            raise ValueError(f"{name} contains a NUL separator")
        if len(value) > 1024:
            raise ValueError(f"{name} exceeds observation identifier budget")
        try:
            nbytes = len(value.encode("utf-8", errors="strict"))
        except UnicodeError as exc:
            raise ValueError(f"{name} is not valid UTF-8 text") from exc
        if nbytes > 1024:
            raise ValueError(f"{name} exceeds observation identifier budget")
    if (
        type(ingested_at_ms) is not int
        or not 0 <= ingested_at_ms <= 2**63 - 1
    ):
        raise ValueError(
            "ingested_at_ms must be a non-negative exact integer within the SQLite range"
        )
    if parent_sha256 is not None and (
        type(parent_sha256) is not str
        or len(parent_sha256) != 64
        or any(character not in "0123456789abcdef" for character in parent_sha256)
    ):
        raise ValueError("parent_sha256 must be an exact lowercase SHA-256 digest")

    # Preserve specific malformed-metadata diagnostics above, but refuse a
    # substituted raw-byte digest BEFORE hashing any otherwise valid payload.
    # This is a local in-process guard, not authenticated capture provenance.
    if hashlib is not _ORIGINAL_HASHLIB or hashlib.sha256 is not _ORIGINAL_SHA256:
        raise ValueError("fixture digest implementation changed before private content hashing")



def _hash_private_fixture(payload: bytes) -> str:
    """Pin the reviewed hasher across the metadata-validation to hash gap.

    In-process hooks can replace hashlib.sha256 *after* metadata preflight.
    Never hand caller-private bytes to that newly installed callback.
    Original SHA-256 is retained at import time; this is not tamper-proof
    sandboxing or authenticated observation provenance.
    """
    _require_original_fixture_budget()
    if hashlib is not _ORIGINAL_HASHLIB or hashlib.sha256 is not _ORIGINAL_SHA256:
        raise ValueError("fixture digest implementation changed before private content hashing")
    digest = _ORIGINAL_SHA256(payload).hexdigest()
    _require_original_fixture_budget()
    if hashlib is not _ORIGINAL_HASHLIB or hashlib.sha256 is not _ORIGINAL_SHA256:
        raise ValueError("fixture digest implementation changed during private content hashing")
    return digest


# A same-process replacement of the *local* hashing helper could otherwise
# receive raw caller-private text or image bytes even when hashlib itself is
# untouched. Refuse that replacement before either fixture hands over data.
_ORIGINAL_PRIVATE_HASH_HELPER = _hash_private_fixture


def _require_original_envelope() -> None:
    # Distinguish constructor substitution from executable field or
    # validator replacement without invoking any of the substitutions.
    if (
        ObservationEnvelope is not _ENVELOPE_TYPE
        or vars(_ENVELOPE_TYPE).get("__init__") is not _ORIGINAL_ENVELOPE_INIT
    ):
        raise ValueError(
            "fixture constructor returned a non-envelope result: class or init changed"
        )
    if vars(_ENVELOPE_TYPE).get("__post_init__") is not _ORIGINAL_ENVELOPE_VALIDATOR:
        raise ValueError(
            "fixture constructor changed during construction: validator definition changed"
        )
    if (
        any(
            vars(_ENVELOPE_TYPE).get(name) is not saved
            for name, saved in zip(
                _ENVELOPE_FIELDS, _ORIGINAL_ENVELOPE_FIELDS, strict=True,
            )
        )
        or any(
            vars(_ENVELOPE_TYPE).get(name) is not saved
            for name, saved in zip(
                _ENVELOPE_HOOKS, _ORIGINAL_ENVELOPE_HOOKS, strict=True,
            )
        )
    ):
        raise ValueError("fixture envelope definition changed before private access")


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
    _require_original_fixture_budget()
    adapter_id = f"fixture:{kind.value}:v1"
    expected = (
        kind, source_id, adapter_id, privacy_scope, ingested_at_ms,
        content_sha256, parent_sha256, 1,
    )
    # An imported constructor symbol can be swapped for an arbitrary callable.
    # Reject it before any forged constructor can run or see fixture metadata.
    # Hashing caller-provided bytes is a callback boundary. Refuse class
    # mutations before any forged result/validator accessor can run.
    _require_original_envelope()
    envelope = ObservationEnvelope(
        kind=kind,
        source_id=source_id,
        adapter_id=adapter_id,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=content_sha256,
        parent_sha256=parent_sha256,
    )
    _require_original_envelope()
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
    _require_original_envelope()
    _VALIDATE_ENVELOPE(envelope)
    _require_original_envelope()
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
    _preflight_fixture_metadata(source_id, privacy_scope, ingested_at_ms, parent_sha256)
    if len(content) > _MAX_FIXTURE_BYTES:
        raise ValueError("fixture content byte budget exceeded")
    try:
        data = content.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("fixture text is not valid UTF-8") from exc
    if len(data) > _MAX_FIXTURE_BYTES:
        raise ValueError("fixture content byte budget exceeded")
    if _hash_private_fixture is not _ORIGINAL_PRIVATE_HASH_HELPER:
        raise ValueError("fixture private digest helper changed before content hashing")
    digest = _hash_private_fixture(data)
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
    _preflight_fixture_metadata(source_id, privacy_scope, ingested_at_ms, parent_sha256)
    if len(payload) > _MAX_FIXTURE_BYTES:
        raise ValueError("fixture content byte budget exceeded")
    if _hash_private_fixture is not _ORIGINAL_PRIVATE_HASH_HELPER:
        raise ValueError("fixture private digest helper changed before content hashing")
    digest = _hash_private_fixture(payload)
    return _sealed_fixture(
        kind=kind,
        source_id=source_id,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=digest,
        parent_sha256=parent_sha256,
    )
