"""Artifact lineage contracts for V3 Candidate/export evidence."""

from __future__ import annotations

import hashlib
import json
import os
import stat
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
        # Identity carriers must be inert, exact built-in values. A subclass
        # can override strip/iteration and change evidence during validation.
        fields = (self.kind, self.path, self.tool_revision)
        if any(
            type(value) is not str
            or not value.strip()
            or len(value) > 4096
            or any(ord(char) < 32 for char in value)
            for value in fields
        ):
            raise ValueError("artifact identity fields required")
        if (
            type(self.sha256) is not str
            or len(self.sha256) != 64
            or any(c not in "0123456789abcdef" for c in self.sha256)
        ):
            raise ValueError("artifact SHA-256 required")
        if type(self.bytes) is not int or self.bytes <= 0:
            raise ValueError("artifact byte size required")


_ARTIFACT_TYPE = ArtifactIdentity


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
        if (
            type(self.schema_version) is not int
            or self.schema_version != 1
            or type(self.quantization) is not str
            or self.quantization != "Q4_K_M"
        ):
            raise ValueError("unsupported lineage schema/quantization")
        for artifact in (
            self.base,
            self.adapter,
            self.merged_hf,
            self.gguf_f32,
            self.gguf_q4km,
            self.paired_base_q4km,
        ):
            if type(artifact) is not _ARTIFACT_TYPE:
                raise ValueError("exact artifact lineage identity required")
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
    """Hash only a stable, single-link local file, never a redirected source.

    Metadata checks mitigate routine path races but cannot establish OS or
    writer authenticity; callers must independently bind the resulting bytes.
    """
    if type(path) is not type(Path(".")) and type(path) is not str:
        raise ValueError("lineage hash path requires an exact local path")
    path = Path(path)
    if ".." in path.parts or len(str(path)) > 4096:
        raise ValueError("lineage hash path must not traverse aliases")

    def epoch(info: os.stat_result) -> tuple[int, ...]:
        return (
            info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns,
        )

    try:
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError("lineage hash path cannot contain symlinks")
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("lineage hash path requires one regular-file link")
        h = hashlib.sha256()
        size = 0
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or epoch(opened) != epoch(before)
            ):
                raise ValueError("lineage hash path changed before reading")
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
                size += len(chunk)
            if epoch(os.fstat(handle.fileno())) != epoch(before):
                raise ValueError("lineage hash path changed during reading")
        after = path.lstat()
        if (
            epoch(after) != epoch(before)
            or size != before.st_size
            or path.is_symlink()
            or any(parent.is_symlink() for parent in path.parents)
        ):
            raise ValueError("lineage hash path changed after reading")
    except OSError as exc:
        raise ValueError("lineage hash path unavailable during verification") from exc
    return h.hexdigest(), size
