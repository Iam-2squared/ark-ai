"""Portable lexical-only Windows SQLite fixture pathname review.

NO filesystem calls, Windows handle creation, junction/reparse-point checks,
hardlink proof, security descriptor checks, or SQLite connection. Strict ASCII
syntax only prevents some ambiguous labels *before* a future OS-specific
design. A matching fingerprint cannot authenticate a file or authorize use.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_DOMAIN = b"ARK-detached-win-sqlite-lexical-v1\0"
_DRIVE = re.compile(r"[A-Z]:\Z")
_COMPONENT = re.compile(r"[a-z0-9][a-z0-9_.-]*\Z")
_RESERVED = frozenset(
    ("con", "prn", "aux", "nul")
    + tuple(f"com{i}" for i in range(1, 10))
    + tuple(f"lpt{i}" for i in range(1, 10))
)
_SUFFIXES = ("-wal", "-shm", "-journal")
_MAX_PATH = 240
_MAX_PART = 80

_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_DRIVE = _DRIVE
_ORIGINAL_COMPONENT = _COMPONENT
_ORIGINAL_RESERVED = _RESERVED
_ORIGINAL_SUFFIXES = _SUFFIXES
_ORIGINAL_LIMITS = (_MAX_PATH, _MAX_PART)


class WindowsSQLiteLexicalRejected(ValueError):
    """This synthetic pathname can denote an ambiguous Windows file label."""


@dataclass(frozen=True, slots=True)
class WindowsSQLiteLexicalReview:
    path_sha256: str
    sidecar_sha256: tuple[str, str, str]
    lexical_fingerprint: str

    @property
    def filesystem_identity_verified(self) -> bool:
        return False

    @property
    def symlink_or_reparse_safety_proven(self) -> bool:
        return False

    @property
    def sqlite_snapshot_coherent(self) -> bool:
        return False

    @property
    def actual_open_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


_RESULT_TYPE = WindowsSQLiteLexicalReview
_RESULT_FIELDS = ("path_sha256", "sidecar_sha256", "lexical_fingerprint")
_DENIALS = (
    "filesystem_identity_verified", "symlink_or_reparse_safety_proven",
    "sqlite_snapshot_coherent", "actual_open_authorized",
    "tool_execution_authorized",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT = tuple(
    vars(_RESULT_TYPE).get(name)
    for name in (*_RESULT_FIELDS, *_DENIALS, *_HOOKS)
)


def _protocol() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_HASH
        or _digest is not _ORIGINAL_DIGEST
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _DRIVE is not _ORIGINAL_DRIVE
        or _COMPONENT is not _ORIGINAL_COMPONENT
        or _RESERVED is not _ORIGINAL_RESERVED
        or _SUFFIXES is not _ORIGINAL_SUFFIXES
        or type(_MAX_PATH) is not int
        or type(_MAX_PART) is not int
        or (_MAX_PATH, _MAX_PART) != _ORIGINAL_LIMITS
        or WindowsSQLiteLexicalReview is not _RESULT_TYPE
        or any(
            vars(_RESULT_TYPE).get(name) is not old
            for name, old in zip(
                (*_RESULT_FIELDS, *_DENIALS, *_HOOKS),
                _ORIGINAL_RESULT, strict=True,
            )
        )
    ):
        raise WindowsSQLiteLexicalRejected("Windows lexical reviewer protocol changed")


def _digest(label: bytes, value: str) -> str:
    _protocol()
    return hashlib.sha256(_DOMAIN + label + value.encode("ascii")).hexdigest()


# The helper receives the full synthetic path. A substitute must never receive
# that caller-provided label, even when the imported hash function is intact.
_ORIGINAL_DIGEST = _digest


def review_windows_sqlite_lexical_path(
    label: str,
) -> WindowsSQLiteLexicalReview:
    """Review a canonical synthetic drive path, never open or normalize it.

    Requires C:\\folder\\store.sqlite3-style exact ASCII spelling.
    Rejects UNC, device namespaces, alternate data streams, 8.3 tildes,
    DOS reserved names (including names with extensions), mixed casing,
    relative components, whitespace and all untrusted expansions.
    """
    _protocol()
    if (
        type(label) is not str
        or not 10 <= len(label) <= _MAX_PATH
        or not label.isascii()
        or "/" in label or "\x00" in label
        or len(label) < 4 or _DRIVE.fullmatch(label[:2]) is None
        or label[2] != "\\"
    ):
        raise WindowsSQLiteLexicalRejected("noncanonical synthetic Windows drive path")
    parts = label[3:].split("\\")
    if (
        len(parts) < 2
        or any(
            not 1 <= len(part) <= _MAX_PART
            or _COMPONENT.fullmatch(part) is None
            or part in (".", "..")
            or part.endswith(".")
            or part.split(".", 1)[0] in _RESERVED
            or "~" in part
            for part in parts
        )
        or not parts[-1].endswith(".sqlite3")
        or parts[-1] == ".sqlite3"
        # The SQLite WAL/SHM/rollback journals are separate pathnames.
        # Accepting the main file at the limit must not silently create a
        # sidecar name beyond the same strict synthetic path budget.
        or any(len(label) + len(suffix) > _MAX_PATH for suffix in _SUFFIXES)
    ):
        raise WindowsSQLiteLexicalRejected("ambiguous synthetic Windows component")
    # This is lexical, NOT a guarantee that all accepted names correspond
    # to distinct Windows filesystem objects or that their ancestors are safe.
    basename = label
    path_digest = _digest(b"main\0", basename)
    sidecars = tuple(
        _digest(b"sidecar\0", basename + suffix) for suffix in _SUFFIXES
    )
    fingerprint = _digest(
        b"bundle\0", path_digest + "\0" + "\0".join(sidecars),
    )
    _protocol()
    result = _RESULT_TYPE(path_digest, sidecars, fingerprint)
    _protocol()
    if (
        type(result) is not _RESULT_TYPE
        or result.path_sha256 != path_digest
        or result.sidecar_sha256 != sidecars
        or result.lexical_fingerprint != fingerprint
        or any(getattr(result, name) is not False for name in _DENIALS)
    ):
        raise WindowsSQLiteLexicalRejected("Windows lexical result gained authority")
    return result
