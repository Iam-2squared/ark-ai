"""Artifact lineage contracts for V3 Candidate/export evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactIdentity:
    kind: str
    path: str
    sha256: str
    bytes: int
    tool_revision: str

    def validate(self) -> None:
        if not self.kind.strip() or not self.path.strip() or not self.tool_revision.strip():
            raise ValueError("artifact identity fields required")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise ValueError("artifact SHA-256 required")
        if self.bytes <= 0:
            raise ValueError("artifact byte size required")


@dataclass(frozen=True)
class CandidateLineage:
    base: ArtifactIdentity
    adapter: ArtifactIdentity
    merged_hf: ArtifactIdentity
    gguf_f32: ArtifactIdentity
    gguf_q4km: ArtifactIdentity
    paired_base_q4km: ArtifactIdentity
    quantization: str = "Q4_K_M"
    schema_version: int = 1

    def validate(self) -> None:
        if self.schema_version != 1 or self.quantization != "Q4_K_M":
            raise ValueError("unsupported lineage schema/quantization")
        for artifact in (
            self.base,
            self.adapter,
            self.merged_hf,
            self.gguf_f32,
            self.gguf_q4km,
            self.paired_base_q4km,
        ):
            artifact.validate()
        if self.gguf_q4km.tool_revision != self.paired_base_q4km.tool_revision:
            raise ValueError("Candidate and paired baseline quantizer revision mismatch")

    def canonical_bytes(self) -> bytes:
        self.validate()
        return (json.dumps(asdict(self), sort_keys=True, separators=(",", ":")) + "\n").encode()

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def hash_file(path: Path) -> tuple[str, int]:
    path = Path(path)
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size
