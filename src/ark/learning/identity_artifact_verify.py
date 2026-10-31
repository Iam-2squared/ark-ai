"""Offline read-only custody check for already-captured V3 identity JSON.

This verifier cannot prove upstream Hugging Face provenance, reviewed data,
consent, external GPU authorization, or permission to train a Candidate.
The expected digest must be pinned independently from the local JSON file.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from .execution import _require_bounded_snapshot_nesting, canonical_json

_MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class LocalIdentityArtifactRejected(ValueError):
    """Reject a changed, aliased, oversized or noncanonical identity artifact."""


@dataclass(frozen=True, slots=True)
class LocalIdentityArtifactWitness:
    artifact_sha256: str
    artifact_bytes: int
    top_level_keys: tuple[str, ...]

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def training_authorized(self) -> bool:
        return False

    @property
    def candidate_generation_authorized(self) -> bool:
        return False

    @property
    def protected_evaluation_authorized(self) -> bool:
        return False


# Bind to the original inert witness class, not a replaced module constructor.
_WITNESS_TYPE = LocalIdentityArtifactWitness


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise LocalIdentityArtifactRejected("duplicate identity JSON key")
        result[name] = value
    return result


def _no_constant(value: str) -> None:
    raise LocalIdentityArtifactRejected(f"invalid identity JSON constant: {value}")


def verify_local_identity_artifact(
    path: Path, *, retained_sha256: str,
) -> LocalIdentityArtifactWitness:
    """Read one local artifact once with bounded canonical-byte verification.

    This closes common file-substitution/alias errors but is not an atomic
    filesystem snapshot or an attestation against an adversarial OS writer.
    """
    if (
        type(path) is not type(Path("."))
        or ".." in path.parts
        or type(retained_sha256) is not str
        or _SHA.fullmatch(retained_sha256) is None
    ):
        raise LocalIdentityArtifactRejected("exact local path and retained digest required")
    try:
        if (
            path.is_symlink()
            or any(parent.is_symlink() for parent in path.parents)
        ):
            raise LocalIdentityArtifactRejected("identity file path may not be symlinked")
        before = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or not 0 < before.st_size <= _MAX_ARTIFACT_BYTES
        ):
            raise LocalIdentityArtifactRejected("identity file type or byte budget invalid")
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                not os.path.samestat(before, opened)
                or opened.st_size != before.st_size
                or opened.st_nlink != 1
            ):
                raise LocalIdentityArtifactRejected("identity file changed before read")
            raw = handle.read(_MAX_ARTIFACT_BYTES + 1)
            after_open = os.fstat(handle.fileno())
            if (
                opened.st_size != after_open.st_size
                or opened.st_mtime_ns != after_open.st_mtime_ns
                or opened.st_nlink != after_open.st_nlink
            ):
                raise LocalIdentityArtifactRejected("identity file changed during read")
        after = path.lstat()
        if (
            not os.path.samestat(before, after)
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or path.is_symlink()
        ):
            raise LocalIdentityArtifactRejected("identity file changed during read")
    except OSError as exc:
        raise LocalIdentityArtifactRejected("identity file unavailable") from exc
    if len(raw) != before.st_size or len(raw) > _MAX_ARTIFACT_BYTES:
        raise LocalIdentityArtifactRejected("identity artifact byte length changed")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != retained_sha256:
        raise LocalIdentityArtifactRejected("identity artifact retained SHA-256 mismatch")
    try:
        _require_bounded_snapshot_nesting(raw)
        parsed = json.loads(
            raw, object_pairs_hook=_unique_pairs, parse_constant=_no_constant,
        )
        if type(parsed) is not dict or canonical_json(parsed) != raw:
            raise LocalIdentityArtifactRejected("identity artifact must be canonical JSON")
    except (UnicodeError, TypeError, ValueError, RecursionError, OverflowError) as exc:
        raise LocalIdentityArtifactRejected("identity artifact JSON rejected") from exc
    # Parse/constructor code may take time, and an accidental writer can
    # replace the path after the earlier post-read check. Recheck the *path*
    # identity before and after witness creation. This is not an atomic FS
    # snapshot and cannot attest to a malicious kernel or concurrent writer.
    def assert_retained_path() -> None:
        try:
            current = path.lstat()
            if (
                not stat.S_ISREG(current.st_mode)
                or not os.path.samestat(before, current)
                or current.st_size != before.st_size
                or current.st_mtime_ns != before.st_mtime_ns
                or current.st_nlink != 1
                or path.is_symlink()
                or any(parent.is_symlink() for parent in path.parents)
            ):
                raise LocalIdentityArtifactRejected(
                    "identity file changed after verified read"
                )
        except OSError as exc:
            raise LocalIdentityArtifactRejected(
                "identity file became unavailable"
            ) from exc

    assert_retained_path()
    result = LocalIdentityArtifactWitness(
        digest, len(raw), tuple(sorted(parsed)),
    )
    if (
        type(result) is not _WITNESS_TYPE
        or result.artifact_sha256 is not digest
        or type(result.artifact_bytes) is not int
        or result.artifact_bytes != len(raw)
        or result.top_level_keys != tuple(sorted(parsed))
        or result.source_authenticated is not False
        or result.training_authorized is not False
        or result.candidate_generation_authorized is not False
        or result.protected_evaluation_authorized is not False
    ):
        raise LocalIdentityArtifactRejected("identity artifact witness changed")
    assert_retained_path()
    # Denial-only witness properties execute callbacks. A property returning
    # False can still rewrite a field of this frozen carrier after the first
    # identity check. Never return a post-denial mixed-epoch witness.
    if (
        type(result) is not _WITNESS_TYPE
        or result.artifact_sha256 is not digest
        or type(result.artifact_bytes) is not int
        or result.artifact_bytes != len(raw)
        or type(result.top_level_keys) is not tuple
        or result.top_level_keys != tuple(sorted(parsed))
        or any(type(key) is not str for key in result.top_level_keys)
    ):
        raise LocalIdentityArtifactRejected(
            "identity artifact witness changed after authority review"
        )
    assert_retained_path()
    if (
        type(result) is not _WITNESS_TYPE
        or result.artifact_sha256 is not digest
        or result.artifact_bytes != len(raw)
        or result.top_level_keys != tuple(sorted(parsed))
    ):
        raise LocalIdentityArtifactRejected(
            "identity artifact witness changed during final path recheck"
        )
    return result
