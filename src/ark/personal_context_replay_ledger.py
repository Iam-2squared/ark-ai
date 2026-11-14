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
_DDL = (
    "CREATE TABLE context_requests ("
    "seq INTEGER PRIMARY KEY, request_id TEXT NOT NULL UNIQUE, "
    "owner_digest TEXT NOT NULL, context_digest TEXT NOT NULL, "
    "binding_digest TEXT NOT NULL, chain_sha256 TEXT NOT NULL)"
)
_BINDING_TYPE = OfflineContextRequestBinding


class OfflineContextReplayRejected(ValueError):
    """An offline context request already occurred or its receipt is unsafe."""


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
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _WITNESS_HOOKS
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
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_TYPE).get(name) for name in _RECEIPT_HOOKS
)


def _require_original_receipt_constructor() -> None:
    if (
        OfflineContextReplayReceipt is not _RECEIPT_TYPE
        or vars(_RECEIPT_TYPE).get("__init__") is not _ORIGINAL_RECEIPT_INIT
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _RECEIPT_FIELDS, _ORIGINAL_RECEIPT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS, strict=True,
            )
        )
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _RECEIPT_HOOKS, _ORIGINAL_RECEIPT_HOOKS, strict=True,
            )
        )
    ):
        raise OfflineContextReplayRejected(
            "postcommit context receipt authority epoch changed"
        )


def _hash(value: tuple[object, ...]) -> str:
    encoded = json.dumps(
        value, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + encoded).hexdigest()


def genesis_offline_context_replay_witness() -> OfflineContextReplayWitness:
    _require_original_witness_carrier()
    value = OfflineContextReplayWitness(0, _hash(("genesis",)))
    _check_witness(value)
    return value


def _valid(value: object, pattern: re.Pattern[str]) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def _require_original_witness_carrier() -> None:
    # Do not execute replaced slots or allocation hooks before the first
    # witness field read, including in recovery-only and read-only paths.
    if (
        OfflineContextReplayWitness is not _WITNESS_TYPE
        or vars(_WITNESS_TYPE).get("independent_custody_proven")
        is not _ORIGINAL_WITNESS_DENIAL
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for name, original in zip(
                _WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS, strict=True,
            )
        )
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for name, original in zip(
                _WITNESS_HOOKS, _ORIGINAL_WITNESS_HOOKS, strict=True,
            )
        )
    ):
        raise OfflineContextReplayRejected("invalid exact retained context witness")


def _check_witness(witness: object) -> tuple[int, str]:
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
    # Reject unsafe native pathname/longest SQLite journal sibling before
    # lstat, a caller callback, or any private context ledger connection.
    if (
        os is not _ORIGINAL_OS
        or os.fsencode is not _ORIGINAL_FSENCODE
        or type(_MAX_DB_PATH_BYTES) is not int
        or _MAX_DB_PATH_BYTES != _ORIGINAL_MAX_DB_PATH_BYTES
    ):
        raise OfflineContextReplayRejected("context ledger path admission changed")
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or ".." in path.parts
        or "\x00" in str(path)
        or path.name in ("", ".", "..")
    ):
        raise OfflineContextReplayRejected("exact absolute local context ledger path required")
    try:
        encoded_length = len(os.fsencode(path))
    except (UnicodeError, ValueError, OSError) as exc:
        raise OfflineContextReplayRejected("context ledger path encoding unavailable") from exc
    if encoded_length + len(b"-journal") > _MAX_DB_PATH_BYTES:
        raise OfflineContextReplayRejected("context ledger path byte budget exceeded")
    try:
        for ancestor in path.parents:
            info = ancestor.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise OfflineContextReplayRejected("context ledger ancestor is unsafe")
        main_absent = False
        try:
            info = path.lstat()
        except FileNotFoundError:
            main_absent = True
            if not create:
                raise OfflineContextReplayRejected("context ledger is missing") from None
        else:
            if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise OfflineContextReplayRejected("existing or aliased context ledger path")
        # SQLite can also open companion journal/WAL/shared-memory files.
        # An otherwise safe main path is not safe when one of those aliases
        # a foreign private file. For a new ledger, refuse orphan sidecars.
        # These are lstat preflights, NOT atomic directory-handle custody.
        for suffix in ("-wal", "-shm", "-journal"):
            companion = path.with_name(path.name + suffix)
            try:
                sidecar = companion.lstat()
            except FileNotFoundError:
                continue
            if (
                main_absent
                or not stat.S_ISREG(sidecar.st_mode)
                or sidecar.st_nlink != 1
            ):
                raise OfflineContextReplayRejected(
                    "context ledger SQLite sidecar is missing its main file or unsafe"
                )
    except OSError as exc:
        raise OfflineContextReplayRejected("context ledger path unavailable") from exc
    return path


def _schema(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone() != (1,):
        raise OfflineContextReplayRejected("unknown context ledger schema version")
    # Limit private DDL hydration inside the caller's current read/write TX.
    # This is a size/type preflight, not an authenticated source seal.
    schema_count, ddl_bytes = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(length(CAST(sql AS BLOB))),0) "
        "FROM sqlite_master"
    ).fetchone()
    if (type(schema_count) is not int or type(ddl_bytes) is not int
            or not 0 <= schema_count <= 8 or not 0 <= ddl_bytes <= 8192):
        raise OfflineContextReplayRejected("context ledger schema drift: SQL preflight budget")
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.execute(_DDL)
        sql = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(sql)) != tuple(expected.execute(sql)):
            raise OfflineContextReplayRejected("context ledger schema drift")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise OfflineContextReplayRejected("context ledger integrity check failed")


def _inspect(conn: sqlite3.Connection) -> OfflineContextReplayWitness:
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
        "typeof(request_id)!='text' OR length(request_id)!=71 OR "
        "typeof(owner_digest)!='text' OR length(owner_digest)!=64 OR "
        "typeof(context_digest)!='text' OR length(context_digest)!=64 OR "
        "typeof(binding_digest)!='text' OR length(binding_digest)!=64 OR "
        "typeof(chain_sha256)!='text' OR length(chain_sha256)!=64 LIMIT 1"
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

    def __init__(self, path: Path, *, create: bool = False) -> None:
        if type(create) is not bool:
            raise OfflineContextReplayRejected("exact creation option required")
        self._path = _check_path(path, create=create)
        source = self._path
        # Existing replay history is inspected in a read-only snapshot.
        # A RESERVED SQLite writer lock is reserved for explicit creation
        # and later CAS reservation, never merely for restart validation.
        mode = "rwc" if create else "ro"
        with closing(sqlite3.connect(
            self._path.as_uri() + "?mode=" + mode,
            uri=True, timeout=10, isolation_level=None,
        )) as conn:
            conn.execute("BEGIN IMMEDIATE" if create else "BEGIN")
            try:
                if create:
                    if (
                        conn.execute("PRAGMA user_version").fetchone() != (0,)
                        or tuple(conn.execute("SELECT name FROM sqlite_master"))
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
        path = _check_path(self._path, create=False)
        mode = "ro" if read_only else "rw"
        return sqlite3.connect(
            path.as_uri() + "?mode=" + mode, uri=True,
            timeout=10, isolation_level=None,
        )

    def witness(self) -> OfflineContextReplayWitness:
        """Read local history; retain a previous witness outside this ledger."""
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
            except sqlite3.IntegrityError as exc:
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
