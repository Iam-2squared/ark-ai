"""Bounded, read-only byte custody checks for disconnected synthetic files.

A digest and matching metadata do NOT authenticate a file, attest a trusted
clock, prove WAL consistency, grant consent, or authorize any action. Callers
must retain a prior seal in independent custody; this module never persists it.
Only synthetic fixture files are used by its tests.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass, field, fields
from pathlib import Path

_MAX_BYTES = 8 * 1024 * 1024
_MAX_PATH = 4096
_CHUNK = 65536
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-disconnected-file-seal-v1\0"
_METADATA_FIELDS = ("size_bytes", "device", "inode", "mtime_ns", "ctime_ns")


class DisconnectedFileSealRejected(ValueError):
    """The read-only local source is missing, modified or unsafe to inspect."""


@dataclass(frozen=True, slots=True)
class DisconnectedFileSeal:
    path_sha256: str = field(repr=False)
    parent_chain_sha256: str = field(repr=False)
    source_sha256: str
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
    def wal_snapshot_verified(self) -> bool:
        return False

    @property
    def context_disclosure_authorized(self) -> bool:
        return False

    @property
    def file_mutation_authorized(self) -> bool:
        return False


def _path(value: object) -> Path:
    if (
        type(value) is not type(Path("."))
        or not value.is_absolute()
        or not 1 <= len(str(value)) <= _MAX_PATH
        or ".." in value.parts
    ):
        raise DisconnectedFileSealRejected("exact absolute local fixture path required")
    return value


def _parents(path: Path) -> str:
    chain = []
    try:
        for item in reversed(path.parents):
            info = os.lstat(item)
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise DisconnectedFileSealRejected("source ancestor is not a real directory")
            chain.append((str(item), info.st_dev, info.st_ino))
    except OSError as exc:
        raise DisconnectedFileSealRejected("source ancestor unavailable") from exc
    if not chain:
        raise DisconnectedFileSealRejected("source has no parent")
    h = hashlib.sha256()
    h.update(_DOMAIN)
    for name, device, inode in chain:
        h.update(repr((name, device, inode)).encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def _metadata(info: os.stat_result) -> tuple[int, ...]:
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise DisconnectedFileSealRejected("source must be singly linked regular file")
    metadata = (
        info.st_size, info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns,
    )
    if any(type(value) is not int or value < 0 for value in metadata):
        raise DisconnectedFileSealRejected("invalid source metadata")
    if info.st_size > _MAX_BYTES:
        raise DisconnectedFileSealRejected("source exceeds byte budget")
    return metadata


def _different_metadata_fields(
    expected: tuple[int, ...], observed: tuple[int, ...],
) -> str:
    """Give safe, value-free diagnostics when path/handle metadata disagree."""
    return ",".join(
        name for name, before, after in zip(
            _METADATA_FIELDS, expected, observed, strict=True,
        ) if before != after
    )


def _once(path: Path) -> DisconnectedFileSeal:
    parent_first = _parents(path)
    try:
        original = _metadata(os.lstat(path))
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        fd = os.open(path, flags)
    except OSError as exc:
        raise DisconnectedFileSealRejected("local source unavailable or unsafe") from exc
    try:
        handle_initial = _metadata(os.fstat(fd))
        if handle_initial != original:
            names = _different_metadata_fields(original, handle_initial)
            raise DisconnectedFileSealRejected(
                f"source changed before read (metadata fields: {names})"
            )
        digest = hashlib.sha256()
        count = 0
        while True:
            chunk = os.read(fd, min(_CHUNK, _MAX_BYTES - count + 1))
            count += len(chunk)
            if count > _MAX_BYTES:
                raise DisconnectedFileSealRejected("source exceeds read byte budget")
            if not chunk:
                break
            digest.update(chunk)
        if count != original[0] or _metadata(os.fstat(fd)) != original:
            raise DisconnectedFileSealRejected("source changed during read")
    except OSError as exc:
        raise DisconnectedFileSealRejected("local source read failed") from exc
    finally:
        os.close(fd)
    try:
        after = _metadata(os.lstat(path))
    except OSError as exc:
        raise DisconnectedFileSealRejected("source unavailable after read") from exc
    if after != original or _parents(path) != parent_first:
        raise DisconnectedFileSealRejected("source changed after read")
    return DisconnectedFileSeal(
        hashlib.sha256(_DOMAIN + str(path).encode("utf-8")).hexdigest(),
        parent_first, digest.hexdigest(), *original,
    )


def capture_disconnected_file_seal(path: Path) -> DisconnectedFileSeal:
    """Read a bounded synthetic file twice; never execute, modify or authorize."""
    path = _path(path)
    first = _once(path)
    if _once(path) != first:
        raise DisconnectedFileSealRejected("source changed between independent reads")
    return first


def review_disconnected_file_seal(
    path: Path, retained: DisconnectedFileSeal,
) -> DisconnectedFileSeal:
    """Require a caller-retained, exact prior seal across both fresh reads."""
    path = _path(path)
    if type(retained) is not DisconnectedFileSeal:
        raise DisconnectedFileSealRejected("exact prior source seal required")
    pinned = tuple(getattr(retained, item.name) for item in fields(retained))
    if (
        any(type(value) is not str or _SHA.fullmatch(value) is None for value in pinned[:3])
        or any(type(value) is not int or value < 0 for value in pinned[3:])
        or pinned[3] > _MAX_BYTES
    ):
        raise DisconnectedFileSealRejected("invalid retained seal shape")

    def epoch() -> None:
        if any(
            getattr(retained, item.name) is not value
            for item, value in zip(fields(retained), pinned, strict=True)
        ):
            raise DisconnectedFileSealRejected("retained seal changed during review")

    epoch()
    current = _once(path)
    epoch()
    if current != retained:
        raise DisconnectedFileSealRejected("retained seal no longer matches source")
    if _once(path) != current:
        raise DisconnectedFileSealRejected("source changed during repeat inspection")
    epoch()
    return current
