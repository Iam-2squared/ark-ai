"""Durable *synthetic* Personal Context request replay-denial fixture.

Only exact hash identifiers are stored, never context text. Hashes remain
linkable metadata and this SQLite ledger is NOT a consent, revocation,
disclosure, independently custodied audit, or trusted-clock authority.
Local unique reservations do not prove exactly-once external actions.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import stat
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .personal_context_request_binding import OfflineContextRequestBinding

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_REQUEST = re.compile(r"ctxreq_[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-disconnected-context-request-replay-ledger-v1\0"
_MAX_ROWS = 512
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
_RECEIPT_TYPE = OfflineContextReplayReceipt


def _hash(value: tuple[object, ...]) -> str:
    encoded = json.dumps(
        value, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + encoded).hexdigest()


def genesis_offline_context_replay_witness() -> OfflineContextReplayWitness:
    return OfflineContextReplayWitness(0, _hash(("genesis",)))


def _valid(value: object, pattern: re.Pattern[str]) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def _check_witness(witness: object) -> tuple[int, str]:
    if (
        type(witness) is not _WITNESS_TYPE
        or type(witness.count) is not int
        or not 0 <= witness.count <= _MAX_ROWS
        or not _valid(witness.chain_sha256, _SHA)
        or witness.independent_custody_proven is not False
    ):
        raise OfflineContextReplayRejected("invalid exact retained context witness")
    return witness.count, witness.chain_sha256


def _check_binding(binding: object) -> tuple[str, str, str, str]:
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
    return fields


def _check_path(path: object, *, create: bool) -> Path:
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or ".." in path.parts
        or len(str(path)) > 4096
    ):
        raise OfflineContextReplayRejected("exact absolute local context ledger path required")
    try:
        for ancestor in path.parents:
            info = ancestor.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise OfflineContextReplayRejected("context ledger ancestor is unsafe")
        try:
            info = path.lstat()
        except FileNotFoundError:
            if not create:
                raise OfflineContextReplayRejected("context ledger is missing") from None
        else:
            if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise OfflineContextReplayRejected("existing or aliased context ledger path")
    except OSError as exc:
        raise OfflineContextReplayRejected("context ledger path unavailable") from exc
    return path


def _schema(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone() != (1,):
        raise OfflineContextReplayRejected("unknown context ledger schema version")
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.execute(_DDL)
        sql = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(sql)) != tuple(expected.execute(sql)):
            raise OfflineContextReplayRejected("context ledger schema drift")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise OfflineContextReplayRejected("context ledger integrity check failed")


def _inspect(conn: sqlite3.Connection) -> OfflineContextReplayWitness:
    _schema(conn)
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
                if observed != expected:
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
        receipt = OfflineContextReplayReceipt(fields[0], expected)
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
        return receipt
