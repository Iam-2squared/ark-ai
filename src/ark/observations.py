"""Typed content-minimized observation envelopes for local multimodal inputs."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum


class ObservationKind(StrEnum):
    TEXT = "text"
    TRANSCRIPT = "transcript"
    IMAGE = "image"
    SCREEN = "screen"


@dataclass(frozen=True, slots=True)
class ObservationEnvelope:
    kind: ObservationKind
    source_id: str
    adapter_id: str
    privacy_scope: str
    ingested_at_ms: int
    content_sha256: str
    parent_sha256: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        _require_original_identity_carrier()
        if type(self.kind) is not ObservationKind:
            raise TypeError("kind must be an exact ObservationKind")
        for name in ("source_id", "adapter_id", "privacy_scope"):
            value = getattr(self, name)
            if type(value) is not str or not value.strip():
                raise ValueError(
                    f"{name} must be a non-empty exact string"
                )
            # Inert fixture metadata must not carry unbounded raw media or
            # arbitrary-sized identifiers into hashes and downstream reviewers.
            # The envelope crosses digest/serialization boundaries in UTF-8.
            # A 1024-character label can occupy 4096 bytes. Enforce the
            # allocation budget on encoded bytes, not Python code points.
            try:
                encoded_label = value.encode("utf-8", errors="strict")
            except UnicodeError as exc:
                raise ValueError(f"{name} is not valid UTF-8 text") from exc
            if len(encoded_label) > 1024:
                raise ValueError(f"{name} exceeds observation identifier budget")
        if (
            type(self.ingested_at_ms) is not int
            or not 0 <= self.ingested_at_ms <= 2**63 - 1
        ):
            raise ValueError(
                "ingested_at_ms must be a non-negative exact integer "
                "within the SQLite range"
            )
        _digest(self.content_sha256, "content_sha256")
        if self.parent_sha256 is not None:
            _digest(self.parent_sha256, "parent_sha256")
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError(
                "schema_version must be exact integer 1"
            )

    @property
    def observation_id(self) -> str:
        # Check exact import-original slots BEFORE touching any source/privacy
        # field. A slotted dataclass can still have an executable field getter
        # or inherited lookup hook installed on its exact class.
        _require_original_identity_carrier()
        _require_original_digest_implementation()
        if type(self) is not _ENVELOPE_TYPE:
            raise ValueError("observation identity requires exact envelope type")
        # A frozen dataclass is still reflectively mutable. The direct public
        # ID getter must not hash a mixed source/privacy/timestamp epoch when
        # serialization or hashing is intercepted by an adapter fixture.
        original = (
            self.kind, self.source_id, self.adapter_id, self.privacy_scope,
            self.ingested_at_ms, self.content_sha256, self.parent_sha256,
            self.schema_version,
        )

        def assert_epoch() -> None:
            _require_original_identity_carrier()
            _require_original_digest_implementation()
            current = (
                self.kind, self.source_id, self.adapter_id, self.privacy_scope,
                self.ingested_at_ms, self.content_sha256, self.parent_sha256,
                self.schema_version,
            )
            if any(now is not before for now, before in zip(
                current, original, strict=True,
            )):
                raise ValueError("observation identity changed during hashing")

        self.__post_init__()
        assert_epoch()
        (kind, source, adapter, privacy, observed, content, parent, schema) = original
        payload = {
            "adapter_id": adapter,
            "content_sha256": content,
            "ingested_at_ms": observed,
            "kind": kind.value,
            "parent_sha256": parent,
            "privacy_scope": privacy,
            "schema_version": schema,
            "source_id": source,
        }
        encoded = (
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        assert_epoch()
        digest = hashlib.sha256(encoded).hexdigest()
        assert_epoch()
        return "obs_" + digest


_ENVELOPE_TYPE = ObservationEnvelope
_ENVELOPE_FIELDS = (
    "kind", "source_id", "adapter_id", "privacy_scope", "ingested_at_ms",
    "content_sha256", "parent_sha256", "schema_version",
)
_ENVELOPE_HOOKS = (
    "__init__", "__new__", "__getattribute__", "__getattr__",
    "__post_init__", "observation_id",
)
_ORIGINAL_ENVELOPE_FIELDS = tuple(
    vars(_ENVELOPE_TYPE)[name] for name in _ENVELOPE_FIELDS
)
_ORIGINAL_ENVELOPE_HOOKS = tuple(
    vars(_ENVELOPE_TYPE).get(name) for name in _ENVELOPE_HOOKS
)


# The direct public identity getter hashes provenance/privacy labels, not
# just opaque content. Pin the import-time serializer and digest before any
# such labels reach a callback. The envelope initializer does not hash and
# therefore remains independent of this opt-in identity preflight.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_RE = re
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_RE_FULLMATCH = re.fullmatch


def _require_original_digest_implementation() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or re is not _ORIGINAL_RE
        or re.fullmatch is not _ORIGINAL_RE_FULLMATCH
    ):
        raise ValueError("observation identity digest implementation changed")


def _require_original_identity_carrier() -> None:
    # Only local, import-original class descriptors are treated as reviewed
    # metadata access paths. This is a defensive check, not in-process
    # sandboxing, source authentication, or consent/dispatch authorization.
    if (
        ObservationEnvelope is not _ENVELOPE_TYPE
        or any(
            vars(_ENVELOPE_TYPE).get(name) is not original
            for name, original in zip(
                _ENVELOPE_FIELDS, _ORIGINAL_ENVELOPE_FIELDS, strict=True,
            )
        )
        or any(
            vars(_ENVELOPE_TYPE).get(name) is not original
            for name, original in zip(
                _ENVELOPE_HOOKS, _ORIGINAL_ENVELOPE_HOOKS, strict=True,
            )
        )
    ):
        raise ValueError("observation identity definition changed")


def _digest(value: object, name: str) -> None:
    # Refuse a patched matcher before invoking it on a caller-supplied label.
    # Exact width also rejects oversized text without running any regex.
    if re is not _ORIGINAL_RE or re.fullmatch is not _ORIGINAL_RE_FULLMATCH:
        raise ValueError("observation digest matcher changed")
    if (
        type(value) is not str
        or len(value) != 64
        or re.fullmatch(r"[0-9a-f]{64}", value) is None
    ):
        raise ValueError(
            f"{name} must be an exact lowercase SHA-256 digest"
        )
