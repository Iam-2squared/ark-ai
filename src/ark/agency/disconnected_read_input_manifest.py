"""Write-once, digest-only expected READ input artifact (offline; no dispatch).

This file is kept separate from the synthetic SQLite receipt journal. Its
contents are caller-controlled, unauthenticated evidence: preserving its
SHA-256 outside this file is the caller's job. It neither proves execution
nor authorizes replay, tools, external effects, or disclosure.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from .disconnected_read_input_binding_review import (
    ReadInputBindingReview,
    review_detached_read_input_binding,
)
from .disconnected_read_journal import ReadJournalSnapshot, ReadJournalWitness
from .disconnected_read_recovery_schedule import ReadRecoveryStep

_REQUEST = re.compile(r"req_[0-9a-f]{32}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SCHEMA = "ark.synthetic.read.input.manifest.v1"
_DOMAIN = b"ARK-detached-read-input-manifest-v1\0"
_MAX_BYTES = 8192
_MAX_STEPS = 24


class ReadInputManifestRejected(ValueError):
    """A local expected-input artifact is absent, inconsistent or unsafe."""


@dataclass(frozen=True, slots=True)
class ReadInputManifest:
    request_id: str
    expected_inputs: tuple[tuple[str, str], ...]
    artifact_sha256: str

    @property
    def backend_dispatched(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_result_proven(self) -> bool:
        return False


_MANIFEST_TYPE = ReadInputManifest
_FIELDS = ("request_id", "expected_inputs", "artifact_sha256")
_DENIALS = (
    "backend_dispatched", "independent_custody_proven",
    "automatic_replay_authorized", "external_result_proven",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_FIELDS = tuple(vars(_MANIFEST_TYPE)[name] for name in _FIELDS)
_ORIGINAL_DENIALS = tuple(vars(_MANIFEST_TYPE)[name] for name in _DENIALS)
_ORIGINAL_HOOKS = tuple(vars(_MANIFEST_TYPE).get(name) for name in _HOOKS)
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_LOADS = json.loads
_ORIGINAL_REVIEW = review_detached_read_input_binding
# Pin the local format, size limits and identifier regexes as well as the
# serializer: a swapped digest domain or widened parser is not the reviewed
# expected-input contract, even if its resulting artifact is self-consistent.
_ORIGINAL_SCHEMA = _SCHEMA
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_MAX_BYTES = _MAX_BYTES
_ORIGINAL_MAX_STEPS = _MAX_STEPS
_ORIGINAL_REQUEST = _REQUEST
_ORIGINAL_STEP = _STEP
_ORIGINAL_SHA = _SHA


def _authority() -> None:
    if (
        ReadInputManifest is not _MANIFEST_TYPE
        or _SCHEMA is not _ORIGINAL_SCHEMA
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or type(_MAX_BYTES) is not int or _MAX_BYTES != _ORIGINAL_MAX_BYTES
        or type(_MAX_STEPS) is not int or _MAX_STEPS != _ORIGINAL_MAX_STEPS
        or _REQUEST is not _ORIGINAL_REQUEST
        or _STEP is not _ORIGINAL_STEP
        or _SHA is not _ORIGINAL_SHA
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or json.loads is not _ORIGINAL_LOADS
        or review_detached_read_input_binding is not _ORIGINAL_REVIEW
        or any(
            vars(_MANIFEST_TYPE).get(name) is not original
            for names, originals in (
                (_FIELDS, _ORIGINAL_FIELDS),
                (_DENIALS, _ORIGINAL_DENIALS),
                (_HOOKS, _ORIGINAL_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise ReadInputManifestRejected("READ input manifest authority changed")


def _validated_inputs(
    request_id: str, expected_inputs: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    _authority()
    if (
        type(request_id) is not str or _REQUEST.fullmatch(request_id) is None
        or type(expected_inputs) is not tuple
        or len(expected_inputs) > _MAX_STEPS
        or any(
            type(entry) is not tuple or len(entry) != 2
            or type(entry[0]) is not str or _STEP.fullmatch(entry[0]) is None
            or type(entry[1]) is not str or _SHA.fullmatch(entry[1]) is None
            for entry in expected_inputs
        )
    ):
        raise ReadInputManifestRejected("invalid exact READ input claims")
    steps = tuple(step for step, _ in expected_inputs)
    if len(set(steps)) != len(steps):
        raise ReadInputManifestRejected("duplicate READ input step")
    return expected_inputs


def _canonical(value: object) -> bytes:
    _authority()
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def _artifact(request_id: str, inputs: tuple[tuple[str, str], ...]) -> tuple[bytes, str]:
    payload = {
        "schema": _SCHEMA,
        "request_id": request_id,
        "expected_inputs": inputs,
    }
    digest = hashlib.sha256(_DOMAIN + _canonical(payload)).hexdigest()
    envelope = dict(payload, artifact_sha256=digest)
    raw = _canonical(envelope) + b"\n"
    if len(raw) > _MAX_BYTES:
        raise ReadInputManifestRejected("READ input manifest exceeds size budget")
    _authority()
    return raw, digest


def _result(
    request_id: str, inputs: tuple[tuple[str, str], ...], digest: str,
) -> ReadInputManifest:
    _authority()
    result = _MANIFEST_TYPE(request_id, inputs, digest)
    _authority()
    if (
        type(result) is not _MANIFEST_TYPE
        or result.request_id is not request_id
        or result.expected_inputs is not inputs
        or result.artifact_sha256 is not digest
        or any(getattr(result, name) is not False for name in _DENIALS)
    ):
        raise ReadInputManifestRejected("READ input manifest gained authority")
    _authority()
    return result



def _sync_created_manifest_directory(target: Path) -> None:
    """Durably publish the newly created name where directory fsync exists.

    File fsync alone does not guarantee that the directory entry survives a
    power loss. Windows cannot use POSIX directory-fd fsync here; callers must
    not infer equivalent crash durability from that platform.
    """
    if os.name != "posix":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(target.parent, flags)
        try:
            if not stat.S_ISDIR(os.fstat(fd).st_mode):
                raise ReadInputManifestRejected("READ input manifest parent is not directory")
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        # Never unlink/retry an artifact whose write or publication is UNKNOWN.
        raise ReadInputManifestRejected("READ input manifest parent sync refused") from exc


def _identity(info: os.stat_result) -> tuple[int, int, int, int]:
    """Stable identity across file handles and named stats, including Windows."""
    return info.st_dev, info.st_ino, info.st_size, info.st_nlink


def _epoch(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
    """Compare timestamps only between observations from the same API source."""
    return (*_identity(info), info.st_mtime_ns, info.st_ctime_ns)


def _safe_manifest_path(path: str | Path) -> Path:
    """Reject symbolic/lexical parent escapes before any manifest file I/O.

    O_NOFOLLOW protects only the final component. This check also refuses
    symlinked ancestor directories and relative traversal. It is a local
    preflight, NOT an atomic dirfd custody guarantee against rename races.
    """
    if type(path) not in (str, type(Path("."))):
        raise ReadInputManifestRejected("READ input manifest requires exact local path")
    target = Path(path)
    if not target.is_absolute() or ".." in target.parts:
        raise ReadInputManifestRejected(
            "READ input manifest requires absolute path without parent traversal"
        )
    try:
        for parent in target.parents:
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ReadInputManifestRejected(
                    "READ input manifest ancestor is not a real directory"
                )
        if target.is_symlink():
            raise ReadInputManifestRejected("READ input manifest symlink refused")
    except OSError as exc:
        raise ReadInputManifestRejected(
            "READ input manifest ancestor cannot be verified"
        ) from exc
    return target


def write_read_input_manifest_once(
    path: str | Path,
    request_id: str,
    expected_inputs: tuple[tuple[str, str], ...],
) -> ReadInputManifest:
    """Create a separate digest-only artifact, never replace an existing path.

    O_EXCL rejects competing creators and preexisting symlinks. A failed or
    interrupted write may leave a partial file: preserve and quarantine it;
    never truncate/retry it implicitly. This is NOT a cross-file transaction.
    """
    inputs = _validated_inputs(request_id, expected_inputs)
    raw, digest = _artifact(request_id, inputs)
    _authority()
    target = _safe_manifest_path(path)
    _authority()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(target, flags, 0o600)
    except OSError as exc:
        raise ReadInputManifestRejected("READ input manifest creation refused") from exc
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
            created = os.fstat(handle.fileno())
    except BaseException:
        # A possibly partial artifact is intentionally NEVER removed here.
        raise
    _authority()
    _sync_created_manifest_directory(target)
    _authority()
    # A competing rename, unlink or in-place overwrite during publication
    # must not produce a successful receipt for a different named artifact.
    # This is a same-invocation local check, NOT authenticated custody or
    # protection against later edits/replacement by the filesystem owner.
    try:
        current = target.stat(follow_symlinks=False)
    except OSError as exc:
        raise ReadInputManifestRejected(
            "READ input manifest publication cannot be verified"
        ) from exc
    if (
        not stat.S_ISREG(created.st_mode) or created.st_nlink != 1
        or not stat.S_ISREG(current.st_mode) or current.st_nlink != 1
        or _identity(created) != _identity(current)
        or os.name != "nt" and _epoch(created) != _epoch(current)
    ):
        raise ReadInputManifestRejected("READ input manifest changed during publication")
    # Every platform must reopen the newly named artifact and compare all
    # published bytes. A same-length local rewrite can escape inode/size
    # checks; metadata is not a content-integrity witness. Windows descriptor
    # creation timestamps are not always comparable to named stat timestamps.
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(target, flags)
        with os.fdopen(fd, "rb", closefd=True) as handle:
            before = os.fstat(handle.fileno())
            actual = handle.read(_MAX_BYTES + 1)
            after = os.fstat(handle.fileno())
            named = target.stat(follow_symlinks=False)
    except OSError as exc:
        raise ReadInputManifestRejected(
            "READ input manifest publication cannot be verified"
        ) from exc
    if (
        actual != raw or not stat.S_ISREG(after.st_mode)
        or _identity(created) != _identity(before)
        or _epoch(before) != _epoch(after)
        or _identity(after) != _identity(named)
        or os.name != "nt" and (
            _epoch(created) != _epoch(after)
            or _epoch(after) != _epoch(named)
        )
    ):
        raise ReadInputManifestRejected("READ input manifest changed during publication")
    _authority()
    return _result(request_id, inputs, digest)


def load_read_input_manifest(
    path: str | Path, *, expected_sha256: str | None = None,
) -> ReadInputManifest:
    """Read one bounded canonical artifact, optionally binding a retained hash.

    The expected hash must come from a *separately retained* trusted source if
    the caller needs tamper evidence. An omitted hash is diagnostic only.
    """
    _authority()
    if expected_sha256 is not None and (
        type(expected_sha256) is not str or _SHA.fullmatch(expected_sha256) is None
    ):
        raise ReadInputManifestRejected("invalid retained artifact SHA-256")
    target = _safe_manifest_path(path)
    _authority()
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        if target.is_symlink():
            raise ReadInputManifestRejected("READ input manifest symlink refused")
        # Two named-file observations catch metadata changes on Windows where
        # descriptor creation timestamps are not always comparable to paths.
        named_before = target.stat(follow_symlinks=False)
        fd = os.open(target, flags)
        with os.fdopen(fd, "rb", closefd=True) as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise ReadInputManifestRejected("READ input manifest is not a regular file")
            raw = handle.read(_MAX_BYTES + 1)
            after = os.fstat(handle.fileno())
            current = target.stat(follow_symlinks=False)
            # Both the descriptor and named path must stay stable during the
            # read. The named path must still refer to the opened inode.
            # These local epochs are NOT independent trusted provenance.
            if (
                not stat.S_ISREG(named_before.st_mode)
                or not stat.S_ISREG(after.st_mode)
                or not stat.S_ISREG(current.st_mode)
                or named_before.st_nlink != 1
                or after.st_nlink != 1 or current.st_nlink != 1
                or _epoch(before) != _epoch(after)
                or _epoch(named_before) != _epoch(current)
                or _identity(before) != _identity(current)
                or os.name != "nt" and _epoch(before) != _epoch(current)
            ):
                raise ReadInputManifestRejected("READ input manifest changed during read")
    except OSError as exc:
        raise ReadInputManifestRejected("READ input manifest read refused") from exc
    _authority()
    if len(raw) > _MAX_BYTES or not raw.endswith(b"\n"):
        raise ReadInputManifestRejected("invalid bounded READ input manifest bytes")
    try:
        data = json.loads(raw.decode("ascii"))
    except (UnicodeError, ValueError, TypeError) as exc:
        raise ReadInputManifestRejected("invalid READ input manifest JSON") from exc
    _authority()
    if (
        type(data) is not dict
        or set(data) != {"schema", "request_id", "expected_inputs", "artifact_sha256"}
        or data["schema"] != _SCHEMA
        or type(data["expected_inputs"]) is not list
        or type(data["artifact_sha256"]) is not str
        or _SHA.fullmatch(data["artifact_sha256"]) is None
    ):
        raise ReadInputManifestRejected("invalid READ input manifest envelope")
    try:
        inputs = tuple(tuple(item) for item in data["expected_inputs"])
    except TypeError as exc:
        raise ReadInputManifestRejected("invalid READ input manifest input rows") from exc
    inputs = _validated_inputs(data["request_id"], inputs)
    canonical, digest = _artifact(data["request_id"], inputs)
    if (
        raw != canonical or data["artifact_sha256"] != digest
        or expected_sha256 is not None and expected_sha256 != digest
    ):
        raise ReadInputManifestRejected("READ input manifest digest/canonical mismatch")
    return _result(data["request_id"], inputs, digest)


def review_persisted_read_input_binding(
    path: str | Path,
    request_id: str,
    steps: tuple[ReadRecoveryStep, ...],
    snapshot: ReadJournalSnapshot,
    retained: ReadJournalWitness,
    *,
    expected_manifest_sha256: str,
) -> ReadInputBindingReview:
    """Read-only join; a digest file never authorizes READ execution or replay."""
    manifest = load_read_input_manifest(path, expected_sha256=expected_manifest_sha256)
    if manifest.request_id != request_id:
        raise ReadInputManifestRejected("READ input manifest request differs")
    _authority()
    result = review_detached_read_input_binding(
        request_id, steps, snapshot, retained, manifest.expected_inputs,
    )
    _authority()
    return result
