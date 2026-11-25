"""Durable *synthetic* Personal Context request replay-denial fixture.

Only exact hash identifiers are stored, never context text. Hashes remain
linkable metadata and this SQLite ledger is NOT a consent, revocation,
disclosure, independently custodied audit, or trusted-clock authority.
Local unique reservations do not prove exactly-once external actions.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .personal_context_request_binding import (
    OfflineContextBindingRejected,
    OfflineContextRequestBinding,
    _assert_original_denials,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_REQUEST = re.compile(r"ctxreq_[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-disconnected-context-request-replay-ledger-v1\0"
_MAX_ROWS = 512
_MAX_DB_PATH_BYTES = 4096
_ORIGINAL_MAX_DB_PATH_BYTES = _MAX_DB_PATH_BYTES
_ORIGINAL_OS = os
_ORIGINAL_FSENCODE = os.fsencode
_ORIGINAL_STAT = stat
_ORIGINAL_STAT_S_ISDIR = stat.S_ISDIR
_ORIGINAL_STAT_S_ISLNK = stat.S_ISLNK
_ORIGINAL_STAT_S_ISREG = stat.S_ISREG
_ORIGINAL_STAT_IFMT = stat.S_IFMT
_FILE_ATTRIBUTE_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_ORIGINAL_FILE_ATTRIBUTE_REPARSE_POINT = _FILE_ATTRIBUTE_REPARSE_POINT


def _is_reparse_point(info: object) -> bool:
    """Recognize POSIX symlinks and Windows reparse-point metadata."""
    _require_original_context_replay_path_policy()
    attributes = getattr(info, "st_file_attributes", 0)
    # Native/fault-injection metadata access can re-enter this module. Check
    # the complete import-time policy again before using the returned value.
    _require_original_context_replay_path_policy()
    return type(attributes) is not int or bool(
        attributes & _ORIGINAL_FILE_ATTRIBUTE_REPARSE_POINT
    )


_ORIGINAL_REPARSE_POINT_CHECK = _is_reparse_point
# The whole local path-admission vector is retained as one identity epoch.
# A jointly replaced stat module, predicates, reparse mask/helper or epoch
# must not make a hostile path classifier appear self-consistent.
_ORIGINAL_CONTEXT_REPLAY_PATH_POLICY_EPOCH = (
    _ORIGINAL_OS,
    _ORIGINAL_FSENCODE,
    _ORIGINAL_MAX_DB_PATH_BYTES,
    _ORIGINAL_STAT,
    _ORIGINAL_STAT_S_ISDIR,
    _ORIGINAL_STAT_S_ISLNK,
    _ORIGINAL_STAT_S_ISREG,
    _ORIGINAL_STAT_IFMT,
    _ORIGINAL_FILE_ATTRIBUTE_REPARSE_POINT,
    _ORIGINAL_REPARSE_POINT_CHECK,
)


def _require_original_context_replay_path_policy(
    *,
    _original_context_replay_path_policy_epoch: tuple[object, ...] = (
        _ORIGINAL_CONTEXT_REPLAY_PATH_POLICY_EPOCH
    ),
) -> None:
    """Reject changed filesystem classifiers before or across path callbacks."""
    epoch = _original_context_replay_path_policy_epoch
    if (
        _ORIGINAL_CONTEXT_REPLAY_PATH_POLICY_EPOCH is not epoch
        or os is not epoch[0]
        or os.fsencode is not epoch[1]
        or _ORIGINAL_OS is not epoch[0]
        or _ORIGINAL_FSENCODE is not epoch[1]
        or type(_MAX_DB_PATH_BYTES) is not int
        or _MAX_DB_PATH_BYTES != epoch[2]
        or _ORIGINAL_MAX_DB_PATH_BYTES is not epoch[2]
        or stat is not epoch[3]
        or _ORIGINAL_STAT is not epoch[3]
        or _ORIGINAL_STAT_S_ISDIR is not epoch[4]
        or _ORIGINAL_STAT_S_ISLNK is not epoch[5]
        or _ORIGINAL_STAT_S_ISREG is not epoch[6]
        or _ORIGINAL_STAT_IFMT is not epoch[7]
        or stat.S_ISDIR is not epoch[4]
        or stat.S_ISLNK is not epoch[5]
        or stat.S_ISREG is not epoch[6]
        or stat.S_IFMT is not epoch[7]
        or getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400) != epoch[8]
        or type(_FILE_ATTRIBUTE_REPARSE_POINT) is not int
        or _FILE_ATTRIBUTE_REPARSE_POINT != epoch[8]
        or _ORIGINAL_FILE_ATTRIBUTE_REPARSE_POINT is not epoch[8]
        or _is_reparse_point is not epoch[9]
        or _ORIGINAL_REPARSE_POINT_CHECK is not epoch[9]
    ):
        raise OfflineContextReplayRejected(
            "context replay path admission changed (policy epoch)"
        )


_ORIGINAL_SQLITE3 = sqlite3
_ORIGINAL_SQLITE_CONNECT = sqlite3.connect
_ORIGINAL_SQLITE_CONNECTION = sqlite3.Connection
_ORIGINAL_SQLITE_INTEGRITY_ERROR = sqlite3.IntegrityError
_DDL = (
    "CREATE TABLE context_requests ("
    "seq INTEGER PRIMARY KEY, request_id TEXT NOT NULL UNIQUE, "
    "owner_digest TEXT NOT NULL, context_digest TEXT NOT NULL, "
    "binding_digest TEXT NOT NULL, chain_sha256 TEXT NOT NULL)"
)
_BINDING_TYPE = OfflineContextRequestBinding


class OfflineContextReplayRejected(ValueError):
    """An offline context request already occurred or its receipt is unsafe."""


# Local hash-chain rules are part of the persisted replay protocol. Reject
# monkey-patched callbacks, format constants and budgets BEFORE path inventory,
# SQLite access, hash input serialization or a retained witness scalar read.
# This is an in-process instrumentation fence, not verified consent, writer
# identity, clock trust or independent storage custody.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_RE = re
_ORIGINAL_SHA = _SHA
_ORIGINAL_REQUEST = _REQUEST
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_DDL = _DDL
_ORIGINAL_MAX_ROWS = _MAX_ROWS


def _require_original_replay_protocol() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or sqlite3 is not _ORIGINAL_SQLITE3
        or _ORIGINAL_SQLITE3.connect is not _ORIGINAL_SQLITE_CONNECT
        or _ORIGINAL_SQLITE3.Connection is not _ORIGINAL_SQLITE_CONNECTION
        or _ORIGINAL_SQLITE3.IntegrityError is not _ORIGINAL_SQLITE_INTEGRITY_ERROR
        or _connect_original is not _ORIGINAL_CONNECT_HELPER
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_DUMPS
        or re is not _ORIGINAL_RE
        or _SHA is not _ORIGINAL_SHA
        or _REQUEST is not _ORIGINAL_REQUEST
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _DDL is not _ORIGINAL_DDL
        or type(_MAX_ROWS) is not int
        or _MAX_ROWS != _ORIGINAL_MAX_ROWS
    ):
        raise OfflineContextReplayRejected(
            "context replay protocol authority changed"
        )


def _connect_original(*args, **kwargs) -> sqlite3.Connection:
    """Open only through the import-original SQLite factory and exact type."""
    _require_original_replay_protocol()
    connection = _ORIGINAL_SQLITE_CONNECT(*args, **kwargs)
    _require_original_replay_protocol()
    if type(connection) is not _ORIGINAL_SQLITE_CONNECTION:
        raise OfflineContextReplayRejected(
            "context ledger SQLite connection type changed"
        )
    return connection


_ORIGINAL_CONNECT_HELPER = _connect_original


@dataclass(frozen=True, slots=True)
class OfflineContextReplayWitness:
    count: int
    chain_sha256: str

    @property
    def independent_custody_proven(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class OfflineContextReplayReceipt:
    request_id: str
    witness: OfflineContextReplayWitness

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def revocation_freshness_verified(self) -> bool:
        return False

    @property
    def context_disclosure_authorized(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_WITNESS_TYPE = OfflineContextReplayWitness
# A False-looking replacement property may still execute code before returning.
# Pin the exact descriptor at import, not at the moment of witness validation.
_ORIGINAL_WITNESS_DENIAL = vars(_WITNESS_TYPE)["independent_custody_proven"]
# The two stored values are slotted dataclass descriptors. A subclass is not
# accepted, but the exact class can still have a field/getter/constructor hook
# replaced at runtime. Pin all originals before touching retained identities.
_WITNESS_FIELDS = ("count", "chain_sha256")
_WITNESS_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_FIELDS
)
_WITNESS_HOOK_ABSENT = object()
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE)[name]
    if name in vars(_WITNESS_TYPE)
    else _WITNESS_HOOK_ABSENT
    for name in _WITNESS_HOOKS
)
_ORIGINAL_WITNESS_EPOCH = (
    _WITNESS_TYPE,
    OfflineContextReplayWitness,
    _WITNESS_FIELDS,
    _WITNESS_HOOKS,
    _ORIGINAL_WITNESS_FIELDS,
    _ORIGINAL_WITNESS_HOOKS,
    _ORIGINAL_WITNESS_DENIAL,
    _WITNESS_HOOK_ABSENT,
)
_RECEIPT_TYPE = OfflineContextReplayReceipt
_RECEIPT_DENIALS = (
    "consent_verified", "revocation_freshness_verified",
    "context_disclosure_authorized", "tool_dispatch_authorized",
    "automatic_replay_authorized",
)
_ORIGINAL_RECEIPT_DENIALS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_DENIALS
)
# Check constructor and slotted fields BEFORE invoking user-replaceable
# class code after COMMIT. This cannot undo a durable reservation.
_RECEIPT_FIELDS = ("request_id", "witness")
_ORIGINAL_RECEIPT_FIELDS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_FIELDS
)
_ORIGINAL_RECEIPT_INIT = vars(_RECEIPT_TYPE)["__init__"]
# A frozen dataclass can still acquire executable lookup/allocation hooks.
# Pin absent as well as present class attributes before post-COMMIT receipt
# construction; a rejected return cannot undo the durable reservation.
_RECEIPT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_RECEIPT_HOOK_ABSENT = object()
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_TYPE)[name]
    if name in vars(_RECEIPT_TYPE)
    else _RECEIPT_HOOK_ABSENT
    for name in _RECEIPT_HOOKS
)
_ORIGINAL_RECEIPT_EPOCH = (
    _RECEIPT_TYPE,
    OfflineContextReplayReceipt,
    _RECEIPT_FIELDS,
    _ORIGINAL_RECEIPT_FIELDS,
    _ORIGINAL_RECEIPT_INIT,
    _RECEIPT_DENIALS,
    _ORIGINAL_RECEIPT_DENIALS,
    _RECEIPT_HOOKS,
    _ORIGINAL_RECEIPT_HOOKS,
    _RECEIPT_HOOK_ABSENT,
)


def _require_original_receipt_constructor(
    *,
    _original_epoch: tuple[object, ...] = _ORIGINAL_RECEIPT_EPOCH,
) -> None:
    if (
        _ORIGINAL_RECEIPT_EPOCH is not _original_epoch
        or _RECEIPT_TYPE is not _original_epoch[0]
        or OfflineContextReplayReceipt is not _original_epoch[1]
        or _RECEIPT_FIELDS is not _original_epoch[2]
        or _ORIGINAL_RECEIPT_FIELDS is not _original_epoch[3]
        or _ORIGINAL_RECEIPT_INIT is not _original_epoch[4]
        or _RECEIPT_DENIALS is not _original_epoch[5]
        or _ORIGINAL_RECEIPT_DENIALS is not _original_epoch[6]
        or _RECEIPT_HOOKS is not _original_epoch[7]
        or _ORIGINAL_RECEIPT_HOOKS is not _original_epoch[8]
        or _RECEIPT_HOOK_ABSENT is not _original_epoch[9]
    ):
        raise OfflineContextReplayRejected(
            "postcommit context receipt authority epoch changed"
        )
    namespace = vars(_RECEIPT_TYPE)
    if (
        "__init__" not in namespace
        or namespace["__init__"] is not _ORIGINAL_RECEIPT_INIT
    ):
        raise OfflineContextReplayRejected(
            "postcommit context receipt authority epoch changed"
        )
    for name, original in zip(
        _RECEIPT_FIELDS, _ORIGINAL_RECEIPT_FIELDS, strict=True,
    ):
        if name not in namespace or namespace[name] is not original:
            raise OfflineContextReplayRejected(
                "postcommit context receipt authority epoch changed"
            )
    for name, original in zip(
        _RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS, strict=True,
    ):
        if name not in namespace or namespace[name] is not original:
            raise OfflineContextReplayRejected(
                "postcommit context receipt authority epoch changed"
            )
    for name, original in zip(
        _RECEIPT_HOOKS, _ORIGINAL_RECEIPT_HOOKS, strict=True,
    ):
        if original is _RECEIPT_HOOK_ABSENT:
            if name in namespace:
                raise OfflineContextReplayRejected(
                    "postcommit context receipt authority epoch changed"
                )
        elif name not in namespace or namespace[name] is not original:
            raise OfflineContextReplayRejected(
                "postcommit context receipt authority epoch changed"
            )


def _hash(value: tuple[object, ...]) -> str:
    _require_original_replay_protocol()
    encoded = json.dumps(
        value, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    _require_original_replay_protocol()
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    _require_original_replay_protocol()
    return digest


def genesis_offline_context_replay_witness() -> OfflineContextReplayWitness:
    _require_original_witness_carrier()
    value = OfflineContextReplayWitness(0, _hash(("genesis",)))
    _check_witness(value)
    return value


def _valid(value: object, pattern: re.Pattern[str]) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def _require_original_witness_carrier(
    *,
    _original_epoch: tuple[object, ...] = _ORIGINAL_WITNESS_EPOCH,
) -> None:
    # Do not execute replaced slots or allocation hooks before the first
    # witness field read, including in recovery-only and read-only paths.
    if (
        _ORIGINAL_WITNESS_EPOCH is not _original_epoch
        or _WITNESS_TYPE is not _original_epoch[0]
        or OfflineContextReplayWitness is not _original_epoch[1]
        or _WITNESS_FIELDS is not _original_epoch[2]
        or _WITNESS_HOOKS is not _original_epoch[3]
        or _ORIGINAL_WITNESS_FIELDS is not _original_epoch[4]
        or _ORIGINAL_WITNESS_HOOKS is not _original_epoch[5]
        or _ORIGINAL_WITNESS_DENIAL is not _original_epoch[6]
        or _WITNESS_HOOK_ABSENT is not _original_epoch[7]
    ):
        raise OfflineContextReplayRejected("invalid exact retained context witness")
    namespace = vars(_WITNESS_TYPE)
    if (
        "independent_custody_proven" not in namespace
        or namespace["independent_custody_proven"] is not _ORIGINAL_WITNESS_DENIAL
        or any(
            name not in namespace or namespace[name] is not original
            for name, original in zip(
                _WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS, strict=True,
            )
        )
    ):
        raise OfflineContextReplayRejected("invalid exact retained context witness")
    for name, original in zip(
        _WITNESS_HOOKS, _ORIGINAL_WITNESS_HOOKS, strict=True,
    ):
        if original is _WITNESS_HOOK_ABSENT:
            if name in namespace:
                raise OfflineContextReplayRejected(
                    "invalid exact retained context witness"
                )
        elif name not in namespace or namespace[name] is not original:
            raise OfflineContextReplayRejected(
                "invalid exact retained context witness"
            )


def _check_witness(witness: object) -> tuple[int, str]:
    _require_original_replay_protocol()
    # Capture values once and recheck after the denial getter. Even a local
    # synthetic witness may be altered reentrantly; no permission is inferred.
    _require_original_witness_carrier()
    if type(witness) is not _WITNESS_TYPE:
        raise OfflineContextReplayRejected("invalid exact retained context witness")
    count, chain = witness.count, witness.chain_sha256
    if (
        type(count) is not int
        or not 0 <= count <= _MAX_ROWS
        or not _valid(chain, _SHA)
        or witness.independent_custody_proven is not False
    ):
        raise OfflineContextReplayRejected("invalid exact retained context witness")
    _require_original_witness_carrier()
    if witness.count is not count or witness.chain_sha256 is not chain:
        raise OfflineContextReplayRejected("retained context witness changed")
    return count, chain


def _check_binding(binding: object) -> tuple[str, str, str, str]:
    _require_original_replay_protocol()
    # The context receipt is hash-only, but exact-class descriptors can be
    # modified into executable callbacks. Reject BEFORE any field/authority
    # access, including on the read-only/restart and CAS reservation paths.
    try:
        _assert_original_denials()
    except OfflineContextBindingRejected as exc:
        raise OfflineContextReplayRejected(
            "untrusted context binding metadata or authority"
        ) from exc
    if type(binding) is not _BINDING_TYPE:
        raise OfflineContextReplayRejected("exact offline context binding required")
    fields = (
        binding.request_id, binding.owner_digest,
        binding.context_digest, binding.binding_digest,
    )
    if (
        not _valid(fields[0], _REQUEST)
        or any(not _valid(item, _SHA) for item in fields[1:])
        or type(binding.record_count) is not int
        or not 1 <= binding.record_count <= 32
        or binding.consent_verified is not False
        or binding.revocation_freshness_verified is not False
        or binding.external_export_authorized is not False
        or binding.tool_dispatch_authorized is not False
        or binding.retention_authorized is not False
    ):
        raise OfflineContextReplayRejected("untrusted context binding metadata or authority")
    # Denial getters remain callbacks even if they return False. Check the
    # import-original class definitions and all pinned fields again.
    try:
        _assert_original_denials()
    except OfflineContextBindingRejected as exc:
        raise OfflineContextReplayRejected(
            "untrusted context binding metadata or authority"
        ) from exc
    if any(now is not old for now, old in zip((
        binding.request_id, binding.owner_digest,
        binding.context_digest, binding.binding_digest,
    ), fields, strict=True)):
        raise OfflineContextReplayRejected("context binding changed during authority check")
    return fields


def _check_path(path: object, *, create: bool) -> Path:
    _require_original_replay_protocol()
    _require_original_context_replay_path_policy()
    # Retain import-original classifiers locally. The module/epoch guard is
    # rechecked after every lstat, metadata accessor and path callback.
    is_directory = _ORIGINAL_STAT_S_ISDIR
    is_symlink = _ORIGINAL_STAT_S_ISLNK
    is_regular = _ORIGINAL_STAT_S_ISREG
    is_reparse_point = _ORIGINAL_REPARSE_POINT_CHECK
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or ".." in path.parts
        or "\x00" in str(path)
        or path.name in ("", ".", "..")
    ):
        raise OfflineContextReplayRejected("exact absolute local context ledger path required")
    try:
        encoded_length = len(_ORIGINAL_FSENCODE(path))
    except (UnicodeError, ValueError, OSError) as exc:
        raise OfflineContextReplayRejected("context ledger path encoding unavailable") from exc
    _require_original_context_replay_path_policy()
    if encoded_length + len(b"-journal") > _MAX_DB_PATH_BYTES:
        raise OfflineContextReplayRejected("context ledger path byte budget exceeded")
    try:
        for ancestor in path.parents:
            _require_original_context_replay_path_policy()
            try:
                info = ancestor.lstat()
            except FileNotFoundError:
                _require_original_context_replay_path_policy()
                raise
            _require_original_context_replay_path_policy()
            mode = info.st_mode
            _require_original_context_replay_path_policy()
            directory = is_directory(mode)
            _require_original_context_replay_path_policy()
            symlink = is_symlink(mode)
            _require_original_context_replay_path_policy()
            reparse = is_reparse_point(info)
            _require_original_context_replay_path_policy()
            if not directory or symlink or reparse:
                raise OfflineContextReplayRejected(
                    "context ledger symbolic, reparse-point or nondirectory ancestor"
                )

        main_absent = False
        _require_original_context_replay_path_policy()
        try:
            info = path.lstat()
        except FileNotFoundError:
            _require_original_context_replay_path_policy()
            main_absent = True
            if not create:
                raise OfflineContextReplayRejected("context ledger is missing") from None
        else:
            _require_original_context_replay_path_policy()
            mode = info.st_mode
            _require_original_context_replay_path_policy()
            regular = is_regular(mode)
            _require_original_context_replay_path_policy()
            link_count = info.st_nlink
            _require_original_context_replay_path_policy()
            reparse = is_reparse_point(info)
            _require_original_context_replay_path_policy()
            if create or not regular or link_count != 1 or reparse:
                raise OfflineContextReplayRejected(
                    "existing, aliased or reparse-point context ledger path"
                )

        # SQLite can also open companion journal/WAL/shared-memory files.
        # A safe main path is not enough when a sidecar aliases another file
        # or is a Windows reparse point. These lstat checks are not atomic
        # directory-handle custody or protection from concurrent renames.
        for suffix in ("-wal", "-shm", "-journal"):
            _require_original_context_replay_path_policy()
            companion = path.with_name(path.name + suffix)
            _require_original_context_replay_path_policy()
            try:
                sidecar = companion.lstat()
            except FileNotFoundError:
                _require_original_context_replay_path_policy()
                continue
            _require_original_context_replay_path_policy()
            if main_absent:
                raise OfflineContextReplayRejected(
                    "context ledger SQLite sidecar is missing its main file or unsafe"
                )
            sidecar_mode = sidecar.st_mode
            _require_original_context_replay_path_policy()
            sidecar_regular = is_regular(sidecar_mode)
            _require_original_context_replay_path_policy()
            sidecar_links = sidecar.st_nlink
            _require_original_context_replay_path_policy()
            sidecar_reparse = is_reparse_point(sidecar)
            _require_original_context_replay_path_policy()
            if not sidecar_regular or sidecar_links != 1 or sidecar_reparse:
                raise OfflineContextReplayRejected(
                    "context ledger SQLite sidecar is not a single regular non-reparse file"
                )
    except OSError as exc:
        raise OfflineContextReplayRejected("context ledger path unavailable") from exc
    _require_original_context_replay_path_policy()
    return path

def _schema(conn: sqlite3.Connection) -> None:
    _require_original_replay_protocol()
    if conn.execute("PRAGMA user_version").fetchone() != (1,):
        raise OfflineContextReplayRejected("unknown context ledger schema version")
    # Limit private DDL hydration inside the caller's current read/write TX.
    # This is a size/type preflight, not an authenticated source seal.
    # SQL alone does not bound stored catalog identifiers. A malformed or
    # forged sqlite_master name/type/tbl_name can remain huge despite short
    # DDL; bound their cumulative UTF-8 bytes in SQLite before Python
    # materializes even one such private schema row.
    schema_count, ddl_bytes, identity_bytes = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(length(CAST(sql AS BLOB))),0), "
        "COALESCE(SUM(COALESCE(length(CAST(type AS BLOB)),0) "
        "+ COALESCE(length(CAST(name AS BLOB)),0) "
        "+ COALESCE(length(CAST(tbl_name AS BLOB)),0)),0) "
        "FROM sqlite_master"
    ).fetchone()
    if (
        type(schema_count) is not int or type(ddl_bytes) is not int
        or type(identity_bytes) is not int
        or not 0 <= schema_count <= 8
        or not 0 <= ddl_bytes <= 8192
        or not 0 <= identity_bytes <= 8192
    ):
        raise OfflineContextReplayRejected(
            "context ledger schema drift: SQL preflight budget"
        )
    with closing(_connect_original(":memory:")) as expected:
        expected.execute(_DDL)
        sql = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(sql)) != tuple(expected.execute(sql)):
            raise OfflineContextReplayRejected("context ledger schema drift")
    # A malformed database requires denial, not unbounded Python hydration
    # of SQLite corruption diagnostics. At most two rows distinguish clean.
    if conn.execute("PRAGMA quick_check").fetchmany(2) != [("ok",)]:
        raise OfflineContextReplayRejected("context ledger integrity check failed")


def _inspect(conn: sqlite3.Connection) -> OfflineContextReplayWitness:
    _require_original_replay_protocol()
    _require_original_witness_carrier()
    _schema(conn)
    # Fail closed on malformed/off-budget persisted identifiers before Python
    # materializes request-linkable private metadata. Counts and SQLite
    # storage-class/width checks share the caller's existing read/write TX.
    persisted_count = conn.execute(
        "SELECT COUNT(*) FROM context_requests"
    ).fetchone()[0]
    if type(persisted_count) is not int or persisted_count > _MAX_ROWS:
        raise OfflineContextReplayRejected("context replay persisted row budget exceeded")
    malformed = conn.execute(
        "SELECT 1 FROM context_requests WHERE "
        "typeof(request_id)!='text' "
        "OR length(CAST(request_id AS BLOB))!=71 OR "
        "typeof(owner_digest)!='text' "
        "OR length(CAST(owner_digest AS BLOB))!=64 OR "
        "typeof(context_digest)!='text' "
        "OR length(CAST(context_digest AS BLOB))!=64 OR "
        "typeof(binding_digest)!='text' "
        "OR length(CAST(binding_digest AS BLOB))!=64 OR "
        "typeof(chain_sha256)!='text' "
        "OR length(CAST(chain_sha256 AS BLOB))!=64 LIMIT 1"
    ).fetchone()
    if malformed is not None:
        raise OfflineContextReplayRejected(
            "context replay persisted identity width or storage type changed"
        )
    current = genesis_offline_context_replay_witness()
    for seq, request, owner, context, binding, chain in conn.execute(
        "SELECT seq,request_id,owner_digest,context_digest,"
        "binding_digest,chain_sha256 FROM context_requests ORDER BY seq"
    ):
        if (
            current.count >= _MAX_ROWS
            or type(seq) is not int or seq != current.count + 1
            or not _valid(request, _REQUEST)
            or any(not _valid(x, _SHA) for x in (owner, context, binding, chain))
        ):
            raise OfflineContextReplayRejected("invalid persisted context request")
        expected = _hash((
            "row", current.chain_sha256, seq, request, owner, context, binding,
        ))
        if chain != expected:
            raise OfflineContextReplayRejected("context request history changed")
        current = OfflineContextReplayWitness(seq, chain)
    return current


class DisconnectedContextReplayLedger:
    """Bounded local reservation journal for synthetic context *identities*."""

    # Keep an instance dictionary for isolated fault-injection wrappers while
    # storing the source path in a data-descriptor slot that cannot be
    # shadowed through vars(instance).
    __slots__ = ("_path", "__dict__")

    def __setattr__(self, name: str, value: object) -> None:
        if name == "_path":
            try:
                object.__getattribute__(self, "_path")
            except AttributeError:
                pass
            else:
                raise AttributeError("context replay ledger path is immutable")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if name == "_path":
            raise AttributeError("context replay ledger path is immutable")
        object.__delattr__(self, name)

    def __init__(self, path: Path, *, create: bool = False) -> None:
        if type(self) is not DisconnectedContextReplayLedger:
            raise OfflineContextReplayRejected("an exact context replay ledger is required")
        if type(create) is not bool:
            raise OfflineContextReplayRejected("exact creation option required")
        self._path = _check_path(path, create=create)
        _require_exact_replay_ledger(self)
        source = self._path
        # Existing replay history is inspected in a read-only snapshot.
        # A RESERVED SQLite writer lock is reserved for explicit creation
        # and later CAS reservation, never merely for restart validation.
        mode = "rwc" if create else "ro"
        with closing(_connect_original(
            self._path.as_uri() + "?mode=" + mode,
            uri=True, timeout=10, isolation_level=None,
        )) as conn:
            conn.execute("BEGIN IMMEDIATE" if create else "BEGIN")
            try:
                if create:
                    if (
                        conn.execute("PRAGMA user_version").fetchone() != (0,)
                        or conn.execute(
                            "SELECT 1 FROM sqlite_master LIMIT 1"
                        ).fetchone() is not None
                    ):
                        raise OfflineContextReplayRejected("new context ledger not empty")
                    conn.execute(_DDL)
                    conn.execute("PRAGMA user_version=1")
                _check_witness(_inspect(conn))
                if self._path is not source:
                    raise OfflineContextReplayRejected("context startup source changed")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _open(self, *, read_only: bool) -> sqlite3.Connection:
        _require_exact_replay_ledger(self)
        path = _check_path(self._path, create=False)
        mode = "ro" if read_only else "rw"
        return _connect_original(
            path.as_uri() + "?mode=" + mode, uri=True,
            timeout=10, isolation_level=None,
        )

    def witness(self) -> OfflineContextReplayWitness:
        """Read local history; retain a previous witness outside this ledger."""
        _require_exact_replay_ledger(self)
        source = self._path
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                current = _inspect(conn)
                _check_witness(current)
                if self._path is not source:
                    raise OfflineContextReplayRejected("context ledger path changed")
                conn.commit()
                _check_witness(current)
                if self._path is not source:
                    raise OfflineContextReplayRejected("context ledger path changed")
                return current
            except BaseException:
                conn.rollback()
                raise

    def verify_retained_prefix(
        self, retained: OfflineContextReplayWitness,
    ) -> OfflineContextReplayWitness:
        """Review a retained checkpoint against one complete local read snapshot.

        Unlike comparing only the latest tip, a retained prefix may remain
        valid after later reservations. No request is reserved, disclosed,
        authorized or automatically replayed. The retained checkpoint must
        come from outside this SQLite database to detect rewritten history.
        """
        _require_exact_replay_ledger(self)
        prior = _check_witness(retained)
        retained_epoch = (retained.count, retained.chain_sha256)
        path_epoch = self._path

        def stable() -> None:
            if (
                self._path is not path_epoch
                or type(retained) is not _WITNESS_TYPE
                or retained.count is not retained_epoch[0]
                or retained.chain_sha256 is not retained_epoch[1]
                or _check_witness(retained) != prior
            ):
                raise OfflineContextReplayRejected(
                    "retained context prefix changed during review"
                )

        stable()
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                stable()
                # _inspect verifies every row, exact schema, sequence and
                # chained digest before any prefix comparison.
                current = _inspect(conn)
                _check_witness(current)
                stable()
                if prior[0] > current.count:
                    raise OfflineContextReplayRejected(
                        "retained context prefix is beyond durable history"
                    )
                if prior[0] == 0:
                    recorded = genesis_offline_context_replay_witness().chain_sha256
                else:
                    row = conn.execute(
                        "SELECT chain_sha256 FROM context_requests WHERE seq=?",
                        (prior[0],),
                    ).fetchone()
                    if row is None or type(row[0]) is not str:
                        raise OfflineContextReplayRejected(
                            "retained context prefix row is missing"
                        )
                    recorded = row[0]
                stable()
                if recorded != prior[1]:
                    raise OfflineContextReplayRejected(
                        "retained context prefix diverged from durable history"
                    )
                conn.commit()
                stable()
                _check_witness(current)
            except BaseException:
                conn.rollback()
                raise
        stable()
        return current

    def reserve(
        self, binding: OfflineContextRequestBinding,
        *, retained: OfflineContextReplayWitness,
    ) -> OfflineContextReplayReceipt:
        """CAS-reserve one synthetic request; NEVER execute or disclose content."""
        _require_exact_replay_ledger(self)
        fields = _check_binding(binding)
        previous = _check_witness(retained)
        pinned_path = self._path

        def stable() -> None:
            if (
                self._path is not pinned_path
                or type(binding) is not _BINDING_TYPE
                or any(now is not old for now, old in zip(
                    _check_binding(binding), fields, strict=True,
                ))
                or type(retained) is not _WITNESS_TYPE
                or any(now is not old for now, old in zip(
                    _check_witness(retained), previous, strict=True,
                ))
            ):
                raise OfflineContextReplayRejected("context request carriers changed")

        stable()
        with closing(self._open(read_only=False)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                actual = _inspect(conn)
                # Equality of digests does not validate the type or denied
                # authority of the independently observed SQLite witness.
                _check_witness(actual)
                stable()
                if (actual.count, actual.chain_sha256) != previous:
                    raise OfflineContextReplayRejected("stale retained context request history")
                if actual.count >= _MAX_ROWS:
                    raise OfflineContextReplayRejected("context replay ledger full")
                seq = actual.count + 1
                chain = _hash(("row", actual.chain_sha256, seq, *fields))
                conn.execute(
                    "INSERT INTO context_requests VALUES(?,?,?,?,?,?)",
                    (seq, *fields, chain),
                )
                expected = OfflineContextReplayWitness(seq, chain)
                committed_tip = _check_witness(expected)
                if (
                    expected.count is not seq
                    or expected.chain_sha256 is not chain
                ):
                    raise OfflineContextReplayRejected("context committed witness changed")
                stable()
                observed = _inspect(conn)
                _check_witness(observed)
                # Witness class equality is patchable: compare exact scalars
                # obtained from the same SQLite write transaction before
                # COMMIT, so a forged __eq__ cannot accept a wrong chain.
                if (
                    observed.count != committed_tip[0]
                    or observed.chain_sha256 != committed_tip[1]
                ):
                    raise OfflineContextReplayRejected("context reservation integrity mismatch")
                stable()
                conn.commit()
            except _ORIGINAL_SQLITE_INTEGRITY_ERROR as exc:
                conn.rollback()
                raise OfflineContextReplayRejected("duplicate context request identity") from exc
            except BaseException:
                conn.rollback()
                raise

        # COMMIT is already durable locally; a postcommit callback failure
        # must never be described as a rollback or retried automatically.
        def stable_witness() -> None:
            if (
                type(expected) is not _WITNESS_TYPE
                or expected.count is not committed_tip[0]
                or expected.chain_sha256 is not committed_tip[1]
                or _check_witness(expected) != committed_tip
            ):
                raise OfflineContextReplayRejected("postcommit context witness changed")

        stable()
        stable_witness()
        _require_original_receipt_constructor()
        receipt = OfflineContextReplayReceipt(fields[0], expected)
        _require_original_receipt_constructor()
        stable()
        stable_witness()
        if (
            type(receipt) is not _RECEIPT_TYPE
            or receipt.request_id is not fields[0]
            or receipt.witness is not expected
            or receipt.consent_verified is not False
            or receipt.revocation_freshness_verified is not False
            or receipt.context_disclosure_authorized is not False
            or receipt.tool_dispatch_authorized is not False
            or receipt.automatic_replay_authorized is not False
        ):
            raise OfflineContextReplayRejected("postcommit context receipt changed")
        # The last False-only getter above is a reentrant callback boundary.
        # Recheck exact committed carriers and original denial declarations,
        # not merely getters which happen to return False. Rejection is
        # AFTER COMMIT and must not authorize a blind retry or disclosure.
        stable()
        stable_witness()
        if (
            type(receipt) is not _RECEIPT_TYPE
            or receipt.request_id is not fields[0]
            or receipt.witness is not expected
            or any(
                vars(_RECEIPT_TYPE).get(name) is not original
                for name, original in zip(
                    _RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS, strict=True,
                )
            )
        ):
            raise OfflineContextReplayRejected(
                "postcommit context receipt authority epoch changed"
            )
        _require_original_receipt_constructor()
        return receipt



def _require_exact_replay_ledger(instance: DisconnectedContextReplayLedger) -> None:
    """Pin the exact replay-ledger type and slot-backed path before SQLite I/O."""
    if type(instance) is not DisconnectedContextReplayLedger:
        raise OfflineContextReplayRejected("an exact context replay ledger is required")
    try:
        path = object.__getattribute__(instance, "_path")
    except AttributeError as exc:
        raise OfflineContextReplayRejected("context replay ledger path is unavailable") from exc
    if type(path) is not type(Path(".")):
        raise OfflineContextReplayRejected("context replay ledger path identity changed")
