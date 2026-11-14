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
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-disconnected-file-seal-v1\0"
_METADATA_FIELDS = ("size_bytes", "device", "inode", "mtime_ns", "ctime_ns")


class DisconnectedFileSealRejected(ValueError):
    """The read-only local source is missing, modified or unsafe to inspect."""


# Local callback identity check only; it does not authenticate source bytes,
# protect against arbitrary code in this process, or grant file/OS authority.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_MAX_BYTES = _MAX_BYTES
_ORIGINAL_MAX_PATH = _MAX_PATH


def _require_original_seal_codec() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or _MAX_BYTES is not _ORIGINAL_MAX_BYTES
        or _MAX_PATH is not _ORIGINAL_MAX_PATH
    ):
        raise DisconnectedFileSealRejected("local file digest or custody budget changed")


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


_SEAL_TYPE = DisconnectedFileSeal
_SEAL_FIELD_NAMES = tuple(item.name for item in fields(_SEAL_TYPE))
_SEAL_DENIAL_NAMES = (
    "independent_custody_proven", "source_authenticated",
    "wal_snapshot_verified", "context_disclosure_authorized",
    "file_mutation_authorized",
)
_SEAL_HOOK_NAMES = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_SEAL_DESCRIPTORS = tuple(
    vars(_SEAL_TYPE).get(name)
    for name in (*_SEAL_FIELD_NAMES, *_SEAL_DENIAL_NAMES, *_SEAL_HOOK_NAMES)
)
_ORIGINAL_FIELD_HELPER = fields
_ORIGINAL_SEAL_FIELD_NAMES = _SEAL_FIELD_NAMES
_ORIGINAL_SEAL_DENIAL_NAMES = _SEAL_DENIAL_NAMES
_ORIGINAL_SEAL_HOOK_NAMES = _SEAL_HOOK_NAMES


def _require_original_seal_carrier() -> None:
    """Reject replaced frozen-field getters, constructors and authority flags.

    Local Python identity checks only; not filesystem custody or consent.
    """
    if (
        DisconnectedFileSeal is not _SEAL_TYPE
        or fields is not _ORIGINAL_FIELD_HELPER
        or _SEAL_FIELD_NAMES is not _ORIGINAL_SEAL_FIELD_NAMES
        or _SEAL_DENIAL_NAMES is not _ORIGINAL_SEAL_DENIAL_NAMES
        or _SEAL_HOOK_NAMES is not _ORIGINAL_SEAL_HOOK_NAMES
        or any(
            vars(_SEAL_TYPE).get(name) is not descriptor
            for name, descriptor in zip(
                (*_SEAL_FIELD_NAMES, *_SEAL_DENIAL_NAMES, *_SEAL_HOOK_NAMES),
                _ORIGINAL_SEAL_DESCRIPTORS, strict=True,
            )
        )
    ):
        raise DisconnectedFileSealRejected("local file seal carrier changed")


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
    _require_original_seal_codec()
    chain = []
    try:
        for item in reversed(path.parents):
            info = os.lstat(item)
            if (not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
                    or getattr(info, "st_file_attributes", 0) & 0x400):
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
    if getattr(info, "st_file_attributes", 0) & 0x400:
        raise DisconnectedFileSealRejected("source reparse point is unsafe")
    # CPython Windows 3.12+ may expose creation time via stat(path).ctime
    # but *change* time via fstat(fd).ctime for the same open file.
    # Compare the portable creation-time carrier on Windows, and separately
    # monitor the handle change time while reading.
    ctime_ns = (
        getattr(info, "st_birthtime_ns", info.st_ctime_ns)
        if os.name == "nt" else info.st_ctime_ns
    )
    metadata = (
        info.st_size, info.st_dev, info.st_ino, info.st_mtime_ns, ctime_ns,
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
    _require_original_seal_codec()
    _require_original_seal_carrier()
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
        initial_handle_info = os.fstat(fd)
        handle_initial = _metadata(initial_handle_info)
        if handle_initial != original:
            names = _different_metadata_fields(original, handle_initial)
            raise DisconnectedFileSealRejected(
                f"source changed before read (metadata fields: {names})"
            )
        _require_original_seal_codec()
        digest = hashlib.sha256()
        count = 0
        while True:
            # One bounded request reduces a mixture of data from different
            # epochs across many 64KiB reads. This is NOT an atomic snapshot.
            chunk = os.read(fd, _MAX_BYTES - count + 1)
            count += len(chunk)
            if count > _MAX_BYTES:
                raise DisconnectedFileSealRejected("source exceeds read byte budget")
            if not chunk:
                break
            digest.update(chunk)
        final_handle_info = os.fstat(fd)
        if (
            count != original[0]
            or _metadata(final_handle_info) != original
            or (os.name == "nt" and
                final_handle_info.st_ctime_ns != initial_handle_info.st_ctime_ns)
        ):
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
    _require_original_seal_codec()
    _require_original_seal_carrier()
    result = DisconnectedFileSeal(
        hashlib.sha256(_DOMAIN + str(path).encode("utf-8")).hexdigest(),
        parent_first, digest.hexdigest(), *original,
    )
    _require_original_seal_carrier()
    return result


def capture_disconnected_file_seal(path: Path) -> DisconnectedFileSeal:
    """Read a bounded synthetic file twice; never execute, modify or authorize."""
    _require_original_seal_codec()
    _require_original_seal_carrier()
    path = _path(path)
    first = _once(path)
    if _once(path) != first:
        raise DisconnectedFileSealRejected("source changed between independent reads")
    return first


def review_disconnected_file_seal(
    path: Path, retained: DisconnectedFileSeal,
) -> DisconnectedFileSeal:
    """Require a caller-retained, exact prior seal across both fresh reads."""
    _require_original_seal_codec()
    _require_original_seal_carrier()
    path = _path(path)
    if type(retained) is not DisconnectedFileSeal:
        raise DisconnectedFileSealRejected("exact prior source seal required")
    pinned = tuple(getattr(retained, name) for name in _SEAL_FIELD_NAMES)
    if (
        any(type(value) is not str or _SHA.fullmatch(value) is None for value in pinned[:3])
        or any(type(value) is not int or value < 0 for value in pinned[3:])
        or pinned[3] > _MAX_BYTES
    ):
        raise DisconnectedFileSealRejected("invalid retained seal shape")

    def epoch() -> None:
        _require_original_seal_carrier()
        if any(
            getattr(retained, name) is not value
            for name, value in zip(_SEAL_FIELD_NAMES, pinned, strict=True)
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
