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


_PIN_TYPE = DisconnectedSourcePin
_PIN_FIELDS = tuple(field.name for field in fields(_PIN_TYPE))
_DENIALS = (
    "independently_attested", "contents_verified",
    "memory_release_authorized", "file_mutation_authorized",
)
_ORIGINAL_DENIALS = tuple(getattr(_PIN_TYPE, key) for key in _DENIALS)
_PIN_HOOK_NAMES = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_PIN_FIELDS = _PIN_FIELDS
_ORIGINAL_DENIAL_NAMES = _DENIALS
_ORIGINAL_DENIAL_DESCRIPTORS = _ORIGINAL_DENIALS
_ORIGINAL_HOOK_NAMES = _PIN_HOOK_NAMES
_ORIGINAL_FIELDS_HELPER = fields
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_MAX_PATH = _MAX_PATH
_ORIGINAL_DESCRIPTORS = tuple(
    vars(_PIN_TYPE).get(name)
    for name in (*_PIN_FIELDS, *_DENIALS, *_PIN_HOOK_NAMES)
)


def _require_original_source_pin_boundary() -> None:
    """Pin local diagnostic carriers before any retained value or path access.

    These same-process checks are fail-closed diagnostics, not independent
    attestation, durable consent, or a grant to open private contents.
    """
    # Preserve the historical denial-specific error while refusing a
    # substituted False-looking descriptor before any file or witness read.
    # New original-carrier tests also require the boundary error marker.
    if (
        DisconnectedSourcePin is _PIN_TYPE
        and _DENIALS is _ORIGINAL_DENIAL_NAMES
        and _ORIGINAL_DENIALS is _ORIGINAL_DENIAL_DESCRIPTORS
        and any(
            vars(_PIN_TYPE).get(name) is not original
            for name, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise DisconnectedSourceRejected(
            "local source pin boundary changed: source pin acquired authority"
        )
    if (
        DisconnectedSourcePin is not _PIN_TYPE
        or fields is not _ORIGINAL_FIELDS_HELPER
        or _PIN_FIELDS is not _ORIGINAL_PIN_FIELDS
        or _DENIALS is not _ORIGINAL_DENIAL_NAMES
        or _ORIGINAL_DENIALS is not _ORIGINAL_DENIAL_DESCRIPTORS
        or _PIN_HOOK_NAMES is not _ORIGINAL_HOOK_NAMES
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _MAX_PATH is not _ORIGINAL_MAX_PATH
        or any(
            vars(_PIN_TYPE).get(name) is not original
            for name, original in zip(
                (*_PIN_FIELDS, *_DENIALS, *_PIN_HOOK_NAMES),
                _ORIGINAL_DESCRIPTORS, strict=True,
            )
        )
    ):
        raise DisconnectedSourceRejected("local source pin boundary changed")



def _pin_values(pin: DisconnectedSourcePin) -> tuple[object, ...]:
    _require_original_source_pin_boundary()
    if type(pin) is not _PIN_TYPE:
        raise DisconnectedSourceRejected("exact source pin required")
    return tuple(getattr(pin, name) for name in _PIN_FIELDS)


def _assert_denied(pin: DisconnectedSourcePin, original: tuple[object, ...]) -> None:
    """Deny-only properties are callbacks; verify each surviving field epoch."""
    _require_original_source_pin_boundary()
    if _pin_values(pin) != original:
        raise DisconnectedSourceRejected("source pin changed during denial")
    for key, descriptor in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True):
        if (
            getattr(_PIN_TYPE, key) is not descriptor
            or getattr(pin, key) is not False
            or _pin_values(pin) != original
        ):
            raise DisconnectedSourceRejected("source pin acquired authority")
    if any(
        getattr(_PIN_TYPE, key) is not descriptor
        for key, descriptor in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
    ) or _pin_values(pin) != original:
        raise DisconnectedSourceRejected("source pin changed during denial")


def _digest(value: object) -> str:
    data = json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(_DOMAIN + data).hexdigest()


def _validated_path(path: object) -> Path:
    _require_original_source_pin_boundary()
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or not 1 <= len(str(path)) <= _MAX_PATH
        or ".." in path.parts
    ):
        raise DisconnectedSourceRejected("exact absolute normalized Path required")
    return path


def _scan(path: Path) -> DisconnectedSourcePin:
    _require_original_source_pin_boundary()
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
    _require_original_source_pin_boundary()
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
    first_values = _pin_values(first)
    _assert_denied(first, first_values)
    second = _scan(path)
    second_values = _pin_values(second)
    if second_values != first_values or _pin_values(first) != first_values:
        raise DisconnectedSourceRejected("file identity changed during capture")
    _assert_denied(second, second_values)
    _assert_denied(first, first_values)
    _require_original_source_pin_boundary()
    return first


def review_disconnected_source(
    path: Path, retained: DisconnectedSourcePin,
) -> DisconnectedSourcePin:
    """Fail closed when file/parent identity differs from retained metadata."""
    path = _validated_path(path)
    if type(retained) is not DisconnectedSourcePin:
        raise DisconnectedSourceRejected("exact retained source pin required")
    pinned = _pin_values(retained)
    if (
        any(type(value) is not str for value in pinned[:2])
        or any(len(value) != 64 for value in pinned[:2])
        or any(c not in "0123456789abcdef" for value in pinned[:2] for c in value)
        or any(type(value) is not int or value < 0 for value in pinned[2:])
    ):
        raise DisconnectedSourceRejected("malformed retained source identity")

    def assert_retained_epoch() -> None:
        if any(
            getattr(retained, name) is not value
            for name, value in zip(_PIN_FIELDS, pinned, strict=True)
        ):
            raise DisconnectedSourceRejected("retained file identity changed during review")

    assert_retained_epoch()
    _assert_denied(retained, pinned)
    first = _scan(path)
    assert_retained_epoch()
    first_values = _pin_values(first)
    if first_values != pinned:
        raise DisconnectedSourceRejected("file or ancestor identity no longer matches")
    _assert_denied(first, first_values)
    assert_retained_epoch()
    second = _scan(path)
    assert_retained_epoch()
    second_values = _pin_values(second)
    if second_values != first_values:
        raise DisconnectedSourceRejected("file identity changed during repeat scan")
    _assert_denied(second, second_values)
    _assert_denied(first, first_values)
    assert_retained_epoch()
    _assert_denied(retained, pinned)
    _require_original_source_pin_boundary()
    return second
