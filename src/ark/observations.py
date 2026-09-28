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
            raise TypeError("kind must be an ObservationKind")
        for name in ("source_id", "adapter_id", "privacy_scope"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if type(self.ingested_at_ms) is not int or self.ingested_at_ms < 0:
            raise ValueError("ingested_at_ms must be a non-negative integer")
        _digest(self.content_sha256, "content_sha256")
        if self.parent_sha256 is not None:
            _digest(self.parent_sha256, "parent_sha256")
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("schema_version must be exactly 1")

    @property
    def observation_id(self) -> str:
        payload = {
            "adapter_id": self.adapter_id,
            "content_sha256": self.content_sha256,
            "ingested_at_ms": self.ingested_at_ms,
            "kind": self.kind.value,
            "parent_sha256": self.parent_sha256,
            "privacy_scope": self.privacy_scope,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
        }
        encoded = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        return "obs_" + hashlib.sha256(encoded).hexdigest()


def _digest(value: object, name: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
