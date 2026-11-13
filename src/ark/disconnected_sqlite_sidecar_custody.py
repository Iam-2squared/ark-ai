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

# Detached metadata can include sensitive absolute fixture paths. Pin the
# digest codec and inventory bounds before any path inspection or callback.
# This detects same-process instrumentation, not hostile code isolation.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_SHA = _SHA
_ORIGINAL_SUFFIXES = _SUFFIXES
_ORIGINAL_MAX_PATH = _MAX_PATH
_ORIGINAL_MAX_FILE_BYTES = _MAX_FILE_BYTES


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


# Frozen instances remain vulnerable to replacement class slot/constructor or
# equality descriptors. Keep all carrier definitions, including deny-only
# properties, anchored to their import-time identity before filesystem access.
_STATE_TYPE = DetachedSQLiteSidecarState
_SEAL_TYPE = DetachedSQLiteSidecarSeal
_STATE_FIELDS = ("suffix", "present", "identity_sha256")
_SEAL_FIELDS = (
    "path_sha256", "directories_sha256", "main_identity_sha256",
    "sidecars", "fingerprint",
)
_DENIAL_FIELDS = (
    "sqlite_transaction_atomicity_proven", "independent_witness_custody_proven",
    "stable_future_path_proven", "consent_verified",
    "tool_execution_authorized",
)
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__", "__eq__")
_STATE_ORIGINALS = tuple(
    vars(_STATE_TYPE).get(key) for key in _STATE_FIELDS + _CARRIER_HOOKS
)
_SEAL_ORIGINALS = tuple(
    vars(_SEAL_TYPE).get(key)
    for key in _SEAL_FIELDS + _CARRIER_HOOKS + _DENIAL_FIELDS
)


def _require_original_carriers() -> None:
    if (
        DetachedSQLiteSidecarState is not _STATE_TYPE
        or DetachedSQLiteSidecarSeal is not _SEAL_TYPE
        or any(
            vars(cls).get(key) is not original
            for cls, keys, originals in (
                (_STATE_TYPE, _STATE_FIELDS + _CARRIER_HOOKS, _STATE_ORIGINALS),
                (_SEAL_TYPE, _SEAL_FIELDS + _CARRIER_HOOKS + _DENIAL_FIELDS,
                 _SEAL_ORIGINALS),
            )
            for key, original in zip(keys, originals, strict=True)
        )
    ):
        raise SQLiteSidecarCustodyRejected("detached SQLite carrier definition changed")


def _seal_snapshot(seal: object) -> tuple[object, ...]:
    """Compare exact primitive evidence; never invoke replaceable dataclass equality."""
    _require_original_codec()
    if type(seal) is not _SEAL_TYPE:
        raise SQLiteSidecarCustodyRejected("malformed retained SQLite sidecar seal")
    head = (
        seal.path_sha256, seal.directories_sha256, seal.main_identity_sha256,
        seal.fingerprint,
    )
    states = seal.sidecars
    if (
        any(type(digest) is not str or _SHA.fullmatch(digest) is None
            for digest in head)
        or type(states) is not tuple or len(states) != len(_SUFFIXES)
    ):
        raise SQLiteSidecarCustodyRejected("malformed retained SQLite sidecar seal")
    normalized = []
    for suffix, state in zip(_SUFFIXES, states, strict=True):
        if (
            type(state) is not _STATE_TYPE
            or type(state.suffix) is not str or state.suffix != suffix
            or type(state.present) is not bool
            or (state.present and (
                type(state.identity_sha256) is not str
                or _SHA.fullmatch(state.identity_sha256) is None
            ))
            or (not state.present and state.identity_sha256 is not None)
        ):
            raise SQLiteSidecarCustodyRejected("malformed retained SQLite sidecar seal")
        normalized.append((state.suffix, state.present, state.identity_sha256))
    return (*head, tuple(normalized))


def _require_original_codec() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _SHA is not _ORIGINAL_SHA
        or _SUFFIXES is not _ORIGINAL_SUFFIXES
        or type(_MAX_PATH) is not int or _MAX_PATH != _ORIGINAL_MAX_PATH
        or type(_MAX_FILE_BYTES) is not int
        or _MAX_FILE_BYTES != _ORIGINAL_MAX_FILE_BYTES
    ):
        raise SQLiteSidecarCustodyRejected(
            "detached SQLite custody codec or inventory bounds changed"
        )
    _require_original_carriers()


def _hash(payload: object) -> str:
    _require_original_codec()
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
    _require_original_codec()
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

        # The final named stat pass can itself be a reentrant boundary.
        # Recheck every still-open main/sidecar descriptor after that pass:
        # an in-place write to a previously checked sidecar must not yield a
        # clean single-sweep seal for its pre-write metadata.
        opened_ids = tuple(_file_id(os.fstat(fd)) for fd in file_fds)
        if opened_ids != tuple(item for item in file_ids if item is not None):
            raise SQLiteSidecarCustodyRejected(
                "SQLite open descriptor changed during inspection"
            )

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
    _require_original_codec()
    source = _path(path)
    first = _capture_once(source)
    first_fields = _seal_snapshot(first)
    second = _capture_once(source)
    if _seal_snapshot(second) != first_fields or _seal_snapshot(first) != first_fields:
        raise SQLiteSidecarCustodyRejected("SQLite sidecar bundle changed between inspections")
    return first


def review_disconnected_sqlite_sidecars(
    path: Path, retained: DetachedSQLiteSidecarSeal,
) -> DetachedSQLiteSidecarSeal:
    """Compare against caller-retained metadata, which is NOT authenticated."""
    _require_original_codec()
    source = _path(path)
    if type(retained) is not DetachedSQLiteSidecarSeal:
        raise SQLiteSidecarCustodyRejected("exact retained SQLite seal required")
    previous_snapshot = _seal_snapshot(retained)
    previous = tuple(getattr(retained, field_.name) for field_ in fields(retained))
    sidecars = previous[3]
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
    if _seal_snapshot(current) != previous_snapshot:
        raise SQLiteSidecarCustodyRejected("retained SQLite sidecar custody differs")
    return current
