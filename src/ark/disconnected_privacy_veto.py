"""One-way, disconnected local privacy veto ledger for synthetic fixtures.

A persisted veto denies reuse; absence of a veto never establishes consent.
Caller-supplied identity digests, clock and independently held witness are not
issuer authentication, trusted time or external revocation evidence. This
module never reads real Memory, exports content or authorizes tool execution.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import stat
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_ROWS = 512
_MAX_MS = 2**63 - 1
_DOMAIN = b"ARK-disconnected-privacy-veto-v1\0"
_DDL = (
    "CREATE TABLE synthetic_privacy_veto ("
    "seq INTEGER PRIMARY KEY, owner_sha256 TEXT NOT NULL, "
    "scope_sha256 TEXT NOT NULL, recorded_at_ms INTEGER NOT NULL, "
    "UNIQUE(owner_sha256, scope_sha256))"
)


class OfflinePrivacyVetoRejected(ValueError):
    """A local fixture veto transition lacks coherent retained evidence."""


@dataclass(frozen=True, slots=True)
class OfflinePrivacyVetoWitness:
    count: int
    fingerprint: str

    @property
    def independent_custody_verified(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class OfflinePrivacyVetoReview:
    local_veto_seen: bool
    witness: OfflinePrivacyVetoWitness

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def context_release_authorized(self) -> bool:
        return False

    @property
    def user_identity_authenticated(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class OfflinePrivacyVetoReceipt:
    owner_sha256: str = field(repr=False)
    scope_sha256: str = field(repr=False)
    recorded_at_ms: int = 0
    witness: OfflinePrivacyVetoWitness | None = None

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def deletion_proven(self) -> bool:
        return False

    @property
    def context_release_authorized(self) -> bool:
        return False


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _ms(value: object) -> bool:
    return type(value) is int and 0 <= value <= _MAX_MS


def _digest(rows: tuple[tuple[object, ...], ...]) -> str:
    encoded = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(_DOMAIN + encoded).hexdigest()


def genesis_privacy_veto_witness() -> OfflinePrivacyVetoWitness:
    return OfflinePrivacyVetoWitness(0, _digest(()))


def _valid_witness(witness: object) -> bool:
    return (
        type(witness) is OfflinePrivacyVetoWitness
        and type(witness.count) is int
        and 0 <= witness.count <= _MAX_ROWS
        and _sha(witness.fingerprint)
    )


def _path(value: object, *, exists: bool) -> Path:
    if type(value) is not type(Path(".")) or not value.is_absolute():
        raise OfflinePrivacyVetoRejected("exact absolute fixture path required")
    if value.is_symlink() or (exists and not value.exists()):
        raise OfflinePrivacyVetoRejected("missing or symbolic veto ledger")
    if value.exists() and not stat.S_ISREG(value.stat(follow_symlinks=False).st_mode):
        raise OfflinePrivacyVetoRejected("veto ledger must be a regular file")
    if not value.parent.is_dir() or value.parent.is_symlink():
        raise OfflinePrivacyVetoRejected("veto parent must be a real directory")
    return value


def _schema(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone() != (1,):
        raise OfflinePrivacyVetoRejected("veto ledger version changed")
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.execute(_DDL)
        query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(query)) != tuple(expected.execute(query)):
            raise OfflinePrivacyVetoRejected("veto ledger schema changed")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise OfflinePrivacyVetoRejected("veto ledger integrity check failed")


def _inspect(conn: sqlite3.Connection) -> OfflinePrivacyVetoWitness:
    _schema(conn)
    rows: list[tuple[object, ...]] = []
    previous = -1
    identities: set[tuple[str, str]] = set()
    for seq, owner, scope, when in conn.execute(
        "SELECT seq,owner_sha256,scope_sha256,recorded_at_ms "
        "FROM synthetic_privacy_veto ORDER BY seq"
    ):
        if (
            len(rows) >= _MAX_ROWS
            or type(seq) is not int or seq != len(rows) + 1
            or not _sha(owner) or not _sha(scope)
            or not _ms(when) or when < previous
            or (owner, scope) in identities
        ):
            raise OfflinePrivacyVetoRejected("malformed or rewritten veto history")
        identities.add((owner, scope))
        rows.append((seq, owner, scope, when))
        previous = when
    return OfflinePrivacyVetoWitness(len(rows), _digest(tuple(rows)))


class DisconnectedPrivacyVetoLedger:
    """Local create-only fixture database, not a consent or identity provider."""

    def __init__(self, path: Path) -> None:
        self._path = _path(path, exists=False)
        with closing(sqlite3.connect(self._path, timeout=10, isolation_level=None)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if tuple(conn.execute("SELECT name FROM sqlite_master")):
                        raise OfflinePrivacyVetoRejected("nonempty unversioned veto ledger")
                    conn.execute(_DDL)
                    conn.execute("PRAGMA user_version=1")
                _inspect(conn)
                if self._path is not path:
                    raise OfflinePrivacyVetoRejected("veto source changed on open")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _open(self, *, read_only: bool) -> sqlite3.Connection:
        path = _path(self._path, exists=True)
        mode = "ro" if read_only else "rw"
        return sqlite3.connect(
            path.as_uri() + "?mode=" + mode, uri=True, timeout=10, isolation_level=None,
        )

    def witness(self) -> OfflinePrivacyVetoWitness:
        """Read source evidence without creating a missing file."""
        source = self._path
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                result = _inspect(conn)
                if self._path is not source:
                    raise OfflinePrivacyVetoRejected("veto source changed during review")
                conn.commit()
                return result
            except BaseException:
                conn.rollback()
                raise

    def review(self, *, owner_sha256: str, scope_sha256: str,
               retained: OfflinePrivacyVetoWitness) -> OfflinePrivacyVetoReview:
        """Report local veto presence; missing veto never permits disclosure."""
        if not _sha(owner_sha256) or not _sha(scope_sha256) or not _valid_witness(retained):
            raise OfflinePrivacyVetoRejected("invalid veto review inputs")
        source = self._path
        epoch = (retained.count, retained.fingerprint)
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                current = _inspect(conn)
                if current != retained or (retained.count, retained.fingerprint) != epoch:
                    raise OfflinePrivacyVetoRejected("stale or rewritten veto evidence")
                rows = tuple(conn.execute(
                    "SELECT seq FROM synthetic_privacy_veto "
                    "WHERE owner_sha256=? AND scope_sha256=?", (owner_sha256, scope_sha256),
                ))
                if len(rows) > 1 or self._path is not source:
                    raise OfflinePrivacyVetoRejected("veto source changed during review")
                if _inspect(conn) != current:
                    raise OfflinePrivacyVetoRejected("veto history changed during review")
                conn.commit()
                return OfflinePrivacyVetoReview(bool(rows), current)
            except BaseException:
                conn.rollback()
                raise

    def veto(self, *, owner_sha256: str, scope_sha256: str, observed_now_ms: int,
             retained: OfflinePrivacyVetoWitness) -> OfflinePrivacyVetoReceipt:
        """Atomically append one local denial marker; never clear or authorize."""
        if (
            not _sha(owner_sha256) or not _sha(scope_sha256)
            or not _ms(observed_now_ms) or not _valid_witness(retained)
        ):
            raise OfflinePrivacyVetoRejected("invalid veto append inputs")
        epoch = (retained.count, retained.fingerprint)
        source = self._path
        with closing(self._open(read_only=False)) as conn:
            if self._path is not source:
                raise OfflinePrivacyVetoRejected("veto source changed before write")
            conn.execute("BEGIN IMMEDIATE")
            try:
                current = _inspect(conn)
                if current != retained or (retained.count, retained.fingerprint) != epoch:
                    raise OfflinePrivacyVetoRejected("stale or rewritten veto evidence")
                if current.count >= _MAX_ROWS:
                    raise OfflinePrivacyVetoRejected("veto ledger full")
                row = conn.execute(
                    "SELECT MAX(recorded_at_ms) FROM synthetic_privacy_veto"
                ).fetchone()
                if row is None or row[0] is not None and observed_now_ms < row[0]:
                    raise OfflinePrivacyVetoRejected("caller clock regressed")
                conn.execute(
                    "INSERT INTO synthetic_privacy_veto VALUES (?,?,?,?)",
                    (current.count + 1, owner_sha256, scope_sha256, observed_now_ms),
                )
                after = _inspect(conn)
                if self._path is not source or (retained.count, retained.fingerprint) != epoch:
                    raise OfflinePrivacyVetoRejected("veto carrier changed before commit")
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise OfflinePrivacyVetoRejected("duplicate local veto") from exc
            except BaseException:
                conn.rollback()
                raise
        return OfflinePrivacyVetoReceipt(owner_sha256, scope_sha256, observed_now_ms, after)
