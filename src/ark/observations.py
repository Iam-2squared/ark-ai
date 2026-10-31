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
            if len(value) > 1024:
                raise ValueError(f"{name} exceeds observation identifier budget")
            try:
                value.encode("utf-8")
            except UnicodeError as exc:
                raise ValueError(f"{name} is not valid UTF-8 text") from exc
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
        # A frozen dataclass is still reflectively mutable. The direct public
        # ID getter must not hash a mixed source/privacy/timestamp epoch when
        # serialization or hashing is intercepted by an adapter fixture.
        original = (
            self.kind, self.source_id, self.adapter_id, self.privacy_scope,
            self.ingested_at_ms, self.content_sha256, self.parent_sha256,
            self.schema_version,
        )

        def assert_epoch() -> None:
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


def _digest(value: object, name: str) -> None:
    if (
        type(value) is not str
        or re.fullmatch(r"[0-9a-f]{64}", value) is None
    ):
        raise ValueError(
            f"{name} must be an exact lowercase SHA-256 digest"
        )
