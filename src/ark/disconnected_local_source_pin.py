"""Read-only file identity continuity checks for detached fixture storage.

Path/inode metadata is neither storage content integrity nor authentication.
No database connection is opened and no user file is created or changed.
A matching result MUST NOT authorize Memory disclosure, dispatch or deletion.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass, field, fields
from pathlib import Path

_DOMAIN = b"ARK-disconnected-source-pin-v1\0"
_MAX_PATH = 4096


class DisconnectedSourceRejected(ValueError):
    """A file carrier cannot be associated with one stable local path epoch."""


@dataclass(frozen=True, slots=True)
class DisconnectedSourcePin:
    path_sha256: str = field(repr=False)
    parent_chain_sha256: str = field(repr=False)
    file_device: int
    file_inode: int
    file_size: int
    file_mtime_ns: int
    parent_device: int
    parent_inode: int

    @property
    def independently_attested(self) -> bool:
        return False

    @property
    def contents_verified(self) -> bool:
        return False

    @property
    def memory_release_authorized(self) -> bool:
        return False

    @property
    def file_mutation_authorized(self) -> bool:
        return False


def _digest(value: object) -> str:
    data = json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(_DOMAIN + data).hexdigest()


def _validated_path(path: object) -> Path:
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or not 1 <= len(str(path)) <= _MAX_PATH
        or ".." in path.parts
    ):
        raise DisconnectedSourceRejected("exact absolute normalized Path required")
    return path


def _scan(path: Path) -> DisconnectedSourcePin:
    # Explicit lstat on each ancestor rejects symlinked parent directories,
    # without following the final path's symlink as Path.stat() would do.
    ancestors = tuple(reversed(path.parents))
    if not ancestors:
        raise DisconnectedSourceRejected("missing source parent")
    chain = []
    try:
        for ancestor in ancestors:
            info = os.lstat(ancestor)
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise DisconnectedSourceRejected("symlink or non-directory source ancestor")
            chain.append((str(ancestor), info.st_dev, info.st_ino))
        source = os.lstat(path)
    except (OSError, ValueError) as exc:
        raise DisconnectedSourceRejected("source or ancestor unavailable") from exc
    if not stat.S_ISREG(source.st_mode) or source.st_nlink != 1:
        raise DisconnectedSourceRejected("source must be singly linked regular file")
    if source.st_size < 0 or source.st_mtime_ns < 0:
        raise DisconnectedSourceRejected("invalid source file metadata")
    return DisconnectedSourcePin(
        path_sha256=_digest(("path", str(path))),
        parent_chain_sha256=_digest(("ancestors", tuple(chain))),
        file_device=source.st_dev,
        file_inode=source.st_ino,
        file_size=source.st_size,
        file_mtime_ns=source.st_mtime_ns,
        parent_device=chain[-1][1],
        parent_inode=chain[-1][2],
    )


def capture_disconnected_source(path: Path) -> DisconnectedSourcePin:
    """Read path metadata twice; a future caller must separately retain it.

    Source bytes, SQLite WAL state, consent and TOCTOU after the second scan
    are NOT covered. This is a fixture continuity diagnostic, not secure-open.
    """
    path = _validated_path(path)
    first = _scan(path)
    second = _scan(path)
    if first != second:
        raise DisconnectedSourceRejected("file identity changed during capture")
    return first


def review_disconnected_source(
    path: Path, retained: DisconnectedSourcePin,
) -> DisconnectedSourcePin:
    """Fail closed when file/parent identity differs from retained metadata."""
    path = _validated_path(path)
    if type(retained) is not DisconnectedSourcePin:
        raise DisconnectedSourceRejected("exact retained source pin required")
    pinned = tuple(getattr(retained, field.name) for field in fields(retained))
    if (
        any(type(value) is not str for value in pinned[:2])
        or any(len(value) != 64 for value in pinned[:2])
        or any(c not in "0123456789abcdef" for value in pinned[:2] for c in value)
        or any(type(value) is not int or value < 0 for value in pinned[2:])
    ):
        raise DisconnectedSourceRejected("malformed retained source identity")

    def assert_retained_epoch() -> None:
        if any(
            getattr(retained, field.name) is not value
            for field, value in zip(fields(retained), pinned, strict=True)
        ):
            raise DisconnectedSourceRejected("retained file identity changed during review")

    assert_retained_epoch()
    first = _scan(path)
    assert_retained_epoch()
    if first != retained:
        raise DisconnectedSourceRejected("file or ancestor identity no longer matches")
    second = _scan(path)
    assert_retained_epoch()
    if second != first:
        raise DisconnectedSourceRejected("file identity changed during repeat scan")
    return second
