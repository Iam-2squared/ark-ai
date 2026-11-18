"""Disconnected, content-minimizing synthetic observation fixture adapter.

This adapter performs NO device access, file I/O, network requests, decoding
or real sensor capture. Its caller supplies small *synthetic* in-memory bytes;
the return value contains only a digest and approved envelope metadata.
Neither the digest nor the fixture adapter ID establishes consent, source
authenticity, trusted clock, or permission to run external tools.
"""

from __future__ import annotations

import hashlib

from . import observations
from .observations import ObservationEnvelope, ObservationKind

_MAX_FIXTURE_BYTES = 65_536
_ADAPTER_ID = "fixture.disconnected.v1"
_ORIGINAL_LIMIT = _MAX_FIXTURE_BYTES
_ORIGINAL_ADAPTER_ID = _ADAPTER_ID
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_KIND = ObservationKind
_ORIGINAL_ENVELOPE = ObservationEnvelope
# The envelope's private metadata validators are imported helpers, not class
# descriptors. Their module bindings must remain original before construction
# reads a source/scope/parent label; replacing them can bypass validation or
# execute a caller-installed callback on those private strings.
_ORIGINAL_IDENTITY_GUARD = observations._require_original_identity_carrier
_ORIGINAL_DIGEST_GUARD = observations._require_original_digest_implementation
_ORIGINAL_DIGEST_VALIDATOR = observations._digest


class DisconnectedFixtureRejected(ValueError):
    """A synthetic fixture was not admitted; no observation was returned."""


def _require_fixture_boundary() -> None:
    if (
        type(_MAX_FIXTURE_BYTES) is not int
        or _MAX_FIXTURE_BYTES != _ORIGINAL_LIMIT
        or _ADAPTER_ID is not _ORIGINAL_ADAPTER_ID
        or hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or ObservationKind is not _ORIGINAL_KIND
        or ObservationEnvelope is not _ORIGINAL_ENVELOPE
        or observations.ObservationEnvelope is not _ORIGINAL_ENVELOPE
        or observations.ObservationKind is not _ORIGINAL_KIND
        or observations._require_original_identity_carrier is not _ORIGINAL_IDENTITY_GUARD
        or observations._require_original_digest_implementation is not _ORIGINAL_DIGEST_GUARD
        or observations._digest is not _ORIGINAL_DIGEST_VALIDATOR
    ):
        raise DisconnectedFixtureRejected("disconnected fixture boundary changed")
    # Class descriptor guards prevent a patched dataclass getter/constructor
    # from being accepted as the original fixture envelope implementation.
    _ORIGINAL_IDENTITY_GUARD()
    _ORIGINAL_DIGEST_GUARD()


def make_disconnected_fixture(
    *,
    kind: ObservationKind,
    source_id: str,
    privacy_scope: str,
    ingested_at_ms: int,
    payload: bytes,
    parent_sha256: str | None = None,
) -> ObservationEnvelope:
    """Hash a bounded synthetic payload into an inert observation envelope.

    This deliberately does not accept a live adapter, device handle, path,
    iterable or generic buffer. In particular, mutable bytearrays and
    objects defining __bytes__ are refused without calling their methods.
    """
    _require_fixture_boundary()
    if type(kind) is not _ORIGINAL_KIND:
        raise DisconnectedFixtureRejected("exact synthetic observation kind required")
    if type(payload) is not bytes or not 1 <= len(payload) <= _MAX_FIXTURE_BYTES:
        raise DisconnectedFixtureRejected("fixture payload must be 1..65536 exact bytes")
    # The disconnected adapter accepts only strict fixture labels. Direct
    # ObservationEnvelope v1 intentionally allows escaped NUL identities;
    # do not change that frozen contract. Reject NUL only at this optional
    # adapter boundary, before any synthetic payload reaches SHA-256.
    if any(
        type(label) is str and "\x00" in label
        for label in (source_id, privacy_scope)
    ):
        raise DisconnectedFixtureRejected("fixture metadata contains NUL separator")
    # Preserve the direct, frozen ObservationEnvelope v1 semantics. Only the
    # opt-in synthetic fixture adapter refuses control-bearing source/privacy
    # labels before envelope construction or hashing private fixture bytes.
    # This avoids ambiguous delimiters in detached review/diagnostic labels.
    if any(
        type(label) is str
        and any(ord(char) < 32 or ord(char) == 127 for char in label)
        for label in (source_id, privacy_scope)
    ):
        raise DisconnectedFixtureRejected("fixture metadata contains ASCII control delimiter")
    # Opt-in fixture identities also deny invisible Unicode formatting,
    # bidi override/isolate markers and non-ASCII line separators. Zero-width
    # identifiers can look identical while producing distinct digest inputs.
    # The public/frozen ObservationEnvelope v1 contract remains unchanged.
    # Do not tighten the public/frozen ObservationEnvelope v1 constructor.
    if any(
        type(label) is str and any(
            codepoint in (0x85, 0x61C, 0x200E, 0x200F, 0x2028, 0x2029)
            or 0x202A <= codepoint <= 0x202E
            or 0x2066 <= codepoint <= 0x2069
            or codepoint in (
                0x00AD, 0x034F, 0x180E, 0x200B, 0x200C, 0x200D,
                0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF,
            )
            or 0x206A <= codepoint <= 0x206F
            for codepoint in map(ord, label)
        )
        for label in (source_id, privacy_scope)
    ):
        raise DisconnectedFixtureRejected("fixture metadata contains Unicode formatting control")
    # First validate the entire public metadata contract using a detached,
    # inert envelope and a fixed digest sentinel. Invalid privacy/source
    # labels, clocks and parent links never cause even a local hashing pass
    # over the caller's private synthetic payload. The preflight object is
    # neither returned nor persisted; the actual digest is filled in below.
    preflight = _ORIGINAL_ENVELOPE(
        kind=kind,
        source_id=source_id,
        adapter_id=_ADAPTER_ID,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256="0" * 64,
        parent_sha256=parent_sha256,
    )
    _require_fixture_boundary()
    if (
        type(preflight) is not _ORIGINAL_ENVELOPE
        or preflight.kind is not kind
        or preflight.content_sha256 != "0" * 64
        or preflight.adapter_id != _ADAPTER_ID
    ):
        raise DisconnectedFixtureRejected("synthetic fixture metadata changed")
    # No raw payload enters the envelope, its identity, logging or audit.
    # Use the imported original callable, not a fresh mutable module lookup.
    # A reentrant swap between preflight and hashing must never receive even
    # synthetic private bytes; the post-hash check still rejects that drift.
    content_hash = _ORIGINAL_SHA256(payload).hexdigest()
    _require_fixture_boundary()
    envelope = _ORIGINAL_ENVELOPE(
        kind=kind,
        source_id=source_id,
        adapter_id=_ADAPTER_ID,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=content_hash,
        parent_sha256=parent_sha256,
    )
    _require_fixture_boundary()
    if (
        type(envelope) is not _ORIGINAL_ENVELOPE
        or envelope.kind is not kind
        or envelope.content_sha256 != content_hash
        or envelope.adapter_id != _ADAPTER_ID
    ):
        raise DisconnectedFixtureRejected("synthetic fixture envelope changed")
    return envelope
