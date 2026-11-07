"""Bounded, read-only POSIX descriptor-anchored custody for synthetic fixtures.

Each path component is opened relative to an already-open directory using
O_NOFOLLOW. This reduces pathname substitution races while taking a snapshot,
but cannot provide a perpetual pathname guarantee or authenticate its owner.
Unsupported platforms fail closed; no OS action or SQLite write is authorized.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, field, fields
from pathlib import Path

_MAX_BYTES = 8 * 1024 * 1024
_MAX_PATH = 4096
_CHUNK = 65536
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-posix-descriptor-custody-v1\0"


class PosixHandleSealRejected(ValueError):
    """A fixture cannot be read through an unambiguous pinned descriptor chain."""


@dataclass(frozen=True, slots=True)
class PosixHandleSeal:
    path_sha256: str = field(repr=False)
    directories_sha256: str = field(repr=False)
    content_sha256: str
    size_bytes: int
    device: int
    inode: int
    mtime_ns: int
    ctime_ns: int

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def durable_snapshot_proven(self) -> bool:
        return False

    @property
    def file_mutation_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


def _digest(value: object) -> str:
    encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(_DOMAIN + encoded).hexdigest()


def _validate_path(path: object) -> Path:
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or not 1 < len(str(path)) <= _MAX_PATH
        or ".." in path.parts
        or len(path.parts) < 2
        or any(not piece or piece in (".", "..") for piece in path.parts[1:])
    ):
        raise PosixHandleSealRejected("exact absolute local fixture file path required")
    return path


def _require_posix() -> None:
    if (
        os.name != "posix"
        or os.open not in os.supports_dir_fd
        or not getattr(os, "O_DIRECTORY", 0)
        or not getattr(os, "O_NOFOLLOW", 0)
    ):
        raise PosixHandleSealRejected("descriptor-anchored opening unsupported here")


def _file_identity(info: os.stat_result) -> tuple[int, ...]:
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise PosixHandleSealRejected("source is not a singly linked regular file")
    result = (
        info.st_size, info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns,
    )
    if any(type(x) is not int or x < 0 for x in result) or info.st_size > _MAX_BYTES:
        raise PosixHandleSealRejected("source metadata outside byte budget")
    return result


def _directory_identity(info: os.stat_result) -> tuple[int, int]:
    if not stat.S_ISDIR(info.st_mode):
        raise PosixHandleSealRejected("non-directory in descriptor chain")
    if any(type(x) is not int or x < 0 for x in (info.st_dev, info.st_ino)):
        raise PosixHandleSealRejected("invalid directory identity")
    return (info.st_dev, info.st_ino)


def _once(path: Path) -> PosixHandleSeal:
    _require_posix()
    # Retain *every* ancestor descriptor until the final pathname recheck.
    # Closing a parent earlier would defeat the directory-relative evidence.
    descriptors: list[int] = []
    names: list[str] = []
    identities: list[tuple[int, int]] = []
    regular_fd: int | None = None
    try:
        directory_flags = (
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptors.append(os.open("/", directory_flags))
        names.append("/")
        identities.append(_directory_identity(os.fstat(descriptors[-1])))
        for component in path.parts[1:-1]:
            fd = os.open(component, directory_flags, dir_fd=descriptors[-1])
            descriptors.append(fd)
            names.append(component)
            identities.append(_directory_identity(os.fstat(fd)))
        file_flags = (
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        regular_fd = os.open(path.name, file_flags, dir_fd=descriptors[-1])
        original = _file_identity(os.fstat(regular_fd))
        digest = hashlib.sha256()
        count = 0
        while True:
            chunk = os.read(regular_fd, min(_CHUNK, _MAX_BYTES - count + 1))
            count += len(chunk)
            if count > _MAX_BYTES:
                raise PosixHandleSealRejected("file exceeded read budget")
            if not chunk:
                break
            digest.update(chunk)
        if count != original[0] or _file_identity(os.fstat(regular_fd)) != original:
            raise PosixHandleSealRejected("file modified during descriptor read")
        # Verify the live names still select these held descriptors, from / down.
        if _directory_identity(os.stat("/", follow_symlinks=False)) != identities[0]:
            raise PosixHandleSealRejected("root changed during read")
        for i in range(1, len(descriptors)):
            observed = os.stat(names[i], dir_fd=descriptors[i - 1],
                               follow_symlinks=False)
            if _directory_identity(observed) != identities[i]:
                raise PosixHandleSealRejected("directory retargeted during read")
        observed_file = os.stat(path.name, dir_fd=descriptors[-1],
                                follow_symlinks=False)
        if _file_identity(observed_file) != original:
            raise PosixHandleSealRejected("source name retargeted during read")
        return PosixHandleSeal(
            path_sha256=_digest(("path", str(path))),
            directories_sha256=_digest(("dirs", tuple(zip(names, identities, strict=True)))),
            content_sha256=digest.hexdigest(),
            size_bytes=original[0],
            device=original[1],
            inode=original[2],
            mtime_ns=original[3],
            ctime_ns=original[4],
        )
    except (OSError, ValueError) as exc:
        if isinstance(exc, PosixHandleSealRejected):
            raise
        raise PosixHandleSealRejected("fixture path or descriptor unavailable") from exc
    finally:
        if regular_fd is not None:
            os.close(regular_fd)
        for fd in reversed(descriptors):
            os.close(fd)


def capture_posix_handle_seal(path: Path) -> PosixHandleSeal:
    """Double-read bounded synthetic bytes; return metadata, never raw content."""
    path = _validate_path(path)
    first = _once(path)
    if _once(path) != first:
        raise PosixHandleSealRejected("source changed between descriptor reads")
    return first


def review_posix_handle_seal(path: Path, retained: PosixHandleSeal) -> PosixHandleSeal:
    """Compare twice against a separately retained seal; never grant authority."""
    path = _validate_path(path)
    if type(retained) is not PosixHandleSeal:
        raise PosixHandleSealRejected("exact retained seal type required")
    original = tuple(getattr(retained, item.name) for item in fields(retained))
    if (
        any(type(x) is not str or _SHA.fullmatch(x) is None for x in original[:3])
        or any(type(x) is not int or x < 0 for x in original[3:])
        or original[3] > _MAX_BYTES
    ):
        raise PosixHandleSealRejected("retained seal has invalid fields")

    def epoch() -> None:
        if any(
            getattr(retained, item.name) is not earlier
            for item, earlier in zip(fields(retained), original, strict=True)
        ):
            raise PosixHandleSealRejected("retained seal changed during inspection")

    epoch()
    first = _once(path)
    epoch()
    if first != retained or _once(path) != first:
        raise PosixHandleSealRejected("current descriptor custody differs from prior seal")
    epoch()
    return first
