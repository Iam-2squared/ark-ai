"""POSIX-only, read-only sidecar inventory for detached synthetic SQLite fixtures.

Descriptor-relative, no-follow opens reduce alias and mid-inspection swap risk.
No SQLite connection is opened and no bytes/row content are read. Even two
matching inspections cannot prove WAL transaction coherence, future pathname
custody, rollback resistance, trustworthy time, or effect authorization.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, field, fields
from pathlib import Path

_DOMAIN = b"ARK-detached-sqlite-sidecar-custody-v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SUFFIXES = ("-wal", "-shm", "-journal")
_MAX_PATH = 4096
_MAX_FILE_BYTES = 64 * 1024 * 1024


class SQLiteSidecarCustodyRejected(ValueError):
    """Synthetic SQLite file/sidecar identities cannot be reviewed safely."""


@dataclass(frozen=True, slots=True)
class DetachedSQLiteSidecarState:
    suffix: str
    present: bool
    identity_sha256: str | None = field(repr=False)


@dataclass(frozen=True, slots=True)
class DetachedSQLiteSidecarSeal:
    path_sha256: str = field(repr=False)
    directories_sha256: str = field(repr=False)
    main_identity_sha256: str = field(repr=False)
    sidecars: tuple[DetachedSQLiteSidecarState, ...]
    fingerprint: str

    @property
    def sqlite_transaction_atomicity_proven(self) -> bool:
        return False

    @property
    def independent_witness_custody_proven(self) -> bool:
        return False

    @property
    def stable_future_path_proven(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(_DOMAIN + encoded).hexdigest()


def _path(value: object) -> Path:
    if (
        type(value) is not type(Path("."))
        or not value.is_absolute()
        or len(str(value)) > _MAX_PATH
        or len(value.parts) < 2
        or ".." in value.parts
        or any(part in ("", ".", "..") for part in value.parts[1:])
    ):
        raise SQLiteSidecarCustodyRejected("exact absolute fixture database Path required")
    return value


def _supported() -> None:
    if (
        os.name != "posix" or os.open not in os.supports_dir_fd
        or os.stat not in os.supports_dir_fd
        or not getattr(os, "O_DIRECTORY", 0)
        or not getattr(os, "O_NOFOLLOW", 0)
    ):
        raise SQLiteSidecarCustodyRejected("safe descriptor-relative review unsupported")


def _dir_id(info: os.stat_result) -> tuple[int, int]:
    if not stat.S_ISDIR(info.st_mode):
        raise SQLiteSidecarCustodyRejected("non-directory in SQLite ancestry")
    fields_ = (info.st_dev, info.st_ino)
    if any(type(value) is not int or value < 0 for value in fields_):
        raise SQLiteSidecarCustodyRejected("invalid SQLite directory metadata")
    return fields_


def _file_id(info: os.stat_result) -> tuple[int, ...]:
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise SQLiteSidecarCustodyRejected("SQLite source must be singly linked regular file")
    values = (
        info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns,
    )
    if any(type(value) is not int or value < 0 for value in values):
        raise SQLiteSidecarCustodyRejected("invalid SQLite file metadata")
    if info.st_size > _MAX_FILE_BYTES:
        raise SQLiteSidecarCustodyRejected("SQLite fixture size budget exceeded")
    return values


def _capture_once(path: Path) -> DetachedSQLiteSidecarSeal:
    _supported()
    dirs: list[int] = []
    dir_names: list[str] = []
    dir_ids: list[tuple[int, int]] = []
    file_fds: list[int] = []
    file_names = (path.name,) + tuple(path.name + suffix for suffix in _SUFFIXES)
    file_ids: list[tuple[int, ...] | None] = []
    try:
        dflags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        dirs.append(os.open("/", dflags))
        dir_names.append("/")
        dir_ids.append(_dir_id(os.fstat(dirs[-1])))
        for name in path.parts[1:-1]:
            dirs.append(os.open(name, dflags, dir_fd=dirs[-1]))
            dir_names.append(name)
            dir_ids.append(_dir_id(os.fstat(dirs[-1])))

        flags = (os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
                 | getattr(os, "O_NONBLOCK", 0))
        for i, name in enumerate(file_names):
            try:
                fd = os.open(name, flags, dir_fd=dirs[-1])
            except FileNotFoundError:
                if i == 0:
                    raise SQLiteSidecarCustodyRejected("main SQLite fixture missing") from None
                file_ids.append(None)
                continue
            file_fds.append(fd)
            file_ids.append(_file_id(os.fstat(fd)))
        if file_ids[0] is None:
            raise SQLiteSidecarCustodyRejected("main SQLite fixture missing")

        # The saved ancestors must still select the same held directories.
        if _dir_id(os.stat("/", follow_symlinks=False)) != dir_ids[0]:
            raise SQLiteSidecarCustodyRejected("root identity changed")
        for i in range(1, len(dirs)):
            actual = os.stat(dir_names[i], dir_fd=dirs[i - 1], follow_symlinks=False)
            if _dir_id(actual) != dir_ids[i]:
                raise SQLiteSidecarCustodyRejected("SQLite directory was retargeted")
        # Recheck absent sidecars, too: creation during inspection is drift.
        for name, expected in zip(file_names, file_ids, strict=True):
            try:
                actual = os.stat(name, dir_fd=dirs[-1], follow_symlinks=False)
            except FileNotFoundError:
                if expected is not None:
                    raise SQLiteSidecarCustodyRejected("SQLite source disappeared") from None
            else:
                if expected is None or _file_id(actual) != expected:
                    raise SQLiteSidecarCustodyRejected("SQLite source retargeted")

        sidecars = tuple(
            DetachedSQLiteSidecarState(suffix, item is not None,
                                       _hash(("sidecar", suffix, item)) if item else None)
            for suffix, item in zip(_SUFFIXES, file_ids[1:], strict=True)
        )
        path_hash = _hash(("path", str(path)))
        ancestry = _hash(("dirs", tuple(zip(dir_names, dir_ids, strict=True))))
        main_hash = _hash(("main", file_ids[0]))
        fingerprint = _hash(("bundle", path_hash, ancestry, main_hash,
                             tuple((s.suffix, s.present, s.identity_sha256) for s in sidecars)))
        return DetachedSQLiteSidecarSeal(path_hash, ancestry, main_hash,
                                         sidecars, fingerprint)
    except OSError as exc:
        raise SQLiteSidecarCustodyRejected("SQLite fixture descriptor unavailable") from exc
    finally:
        for fd in reversed(file_fds):
            os.close(fd)
        for fd in reversed(dirs):
            os.close(fd)


def capture_disconnected_sqlite_sidecars(path: Path) -> DetachedSQLiteSidecarSeal:
    """Inspect synthetic main/-wal/-shm/-journal twice; no row data or writes."""
    source = _path(path)
    first = _capture_once(source)
    if _capture_once(source) != first:
        raise SQLiteSidecarCustodyRejected("SQLite sidecar bundle changed between inspections")
    return first


def review_disconnected_sqlite_sidecars(
    path: Path, retained: DetachedSQLiteSidecarSeal,
) -> DetachedSQLiteSidecarSeal:
    """Compare against caller-retained metadata, which is NOT authenticated."""
    source = _path(path)
    if type(retained) is not DetachedSQLiteSidecarSeal:
        raise SQLiteSidecarCustodyRejected("exact retained SQLite seal required")
    previous = tuple(getattr(retained, field_.name) for field_ in fields(retained))
    sidecars = previous[3]
    if (
        any(type(s) is not str or _SHA.fullmatch(s) is None for s in
            (previous[0], previous[1], previous[2], previous[4]))
        or type(sidecars) is not tuple or len(sidecars) != len(_SUFFIXES)
        or any(
            type(s) is not DetachedSQLiteSidecarState or s.suffix != suffix
            or type(s.present) is not bool
            or (s.present and (type(s.identity_sha256) is not str
                              or _SHA.fullmatch(s.identity_sha256) is None))
            or (not s.present and s.identity_sha256 is not None)
            for suffix, s in zip(_SUFFIXES, sidecars, strict=True)
        )
    ):
        raise SQLiteSidecarCustodyRejected("malformed retained SQLite sidecar seal")
    originals = tuple((s, s.suffix, s.present, s.identity_sha256) for s in sidecars)

    def epoch() -> None:
        if any(getattr(retained, field_.name) is not old
               for field_, old in zip(fields(retained), previous, strict=True)):
            raise SQLiteSidecarCustodyRejected("retained SQLite seal carrier changed")
        if any((s.suffix is not suffix or s.present is not present
                or s.identity_sha256 is not digest)
               for s, suffix, present, digest in originals):
            raise SQLiteSidecarCustodyRejected("retained SQLite sidecar changed")

    epoch()
    current = capture_disconnected_sqlite_sidecars(source)
    epoch()
    if current != retained:
        raise SQLiteSidecarCustodyRejected("retained SQLite sidecar custody differs")
    return current
