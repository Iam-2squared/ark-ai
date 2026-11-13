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
_MAX_PATH = 4096
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


_WITNESS_TYPE = OfflinePrivacyVetoWitness
_WITNESS_FIELDS = ("count", "fingerprint")
_WITNESS_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_FIELDS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _WITNESS_HOOKS
)
_ORIGINAL_WITNESS_INIT = vars(_WITNESS_TYPE)["__init__"]
_ORIGINAL_WITNESS_DENIAL = vars(_WITNESS_TYPE)["independent_custody_verified"]


def _assert_original_witness_carrier() -> None:
    # A frozen dataclass is still mutable at the *class* level. Reject a
    # replaced slot/getter/constructor before inspecting a retained witness
    # or constructing a witness from private SQLite history.
    if (
        OfflinePrivacyVetoWitness is not _WITNESS_TYPE
        or vars(_WITNESS_TYPE).get("__init__") is not _ORIGINAL_WITNESS_INIT
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
        or vars(_WITNESS_TYPE).get("independent_custody_verified")
        is not _ORIGINAL_WITNESS_DENIAL
    ):
        raise OfflinePrivacyVetoRejected("privacy veto witness carrier changed")


_REVIEW_TYPE = OfflinePrivacyVetoReview
_REVIEW_FIELDS = ("local_veto_seen", "witness")
_REVIEW_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REVIEW_FIELDS = tuple(
    vars(_REVIEW_TYPE)[name] for name in _REVIEW_FIELDS
)
_ORIGINAL_REVIEW_HOOKS = tuple(
    vars(_REVIEW_TYPE).get(name) for name in _REVIEW_HOOKS
)
_ORIGINAL_REVIEW_INIT = vars(_REVIEW_TYPE)["__init__"]
_REVIEW_DENIALS = (
    "consent_verified", "context_release_authorized",
    "user_identity_authenticated",
)
_ORIGINAL_REVIEW_DENIALS = tuple(
    vars(_REVIEW_TYPE)[key] for key in _REVIEW_DENIALS
)


def _assert_original_review_denials() -> None:
    # Check import-original class identity, slots, hooks and constructor
    # before opening private fixture state or invoking any deny-only getter.
    _assert_original_witness_carrier()
    if (
        OfflinePrivacyVetoReview is not _REVIEW_TYPE
        or vars(_REVIEW_TYPE).get("__init__") is not _ORIGINAL_REVIEW_INIT
        or any(
            vars(_REVIEW_TYPE).get(name) is not original
            for name, original in zip(
                _REVIEW_FIELDS, _ORIGINAL_REVIEW_FIELDS, strict=True,
            )
        )
        or any(
            vars(_REVIEW_TYPE).get(name) is not original
            for name, original in zip(
                _REVIEW_HOOKS, _ORIGINAL_REVIEW_HOOKS, strict=True,
            )
        )
        or any(
            vars(_REVIEW_TYPE).get(name) is not original
            for name, original in zip(
                _REVIEW_DENIALS, _ORIGINAL_REVIEW_DENIALS, strict=True,
            )
        )
    ):
        raise OfflinePrivacyVetoRejected("privacy veto review acquired authority")

_RECEIPT_TYPE = OfflinePrivacyVetoReceipt
_RECEIPT_DENIALS = (
    "consent_verified", "deletion_proven", "context_release_authorized",
)
_ORIGINAL_RECEIPT_DENIALS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_DENIALS
)
_ORIGINAL_RECEIPT_INIT = vars(_RECEIPT_TYPE)["__init__"]
_RECEIPT_FIELDS = (
    "owner_sha256", "scope_sha256", "recorded_at_ms", "witness",
)
_RECEIPT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RECEIPT_FIELDS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_FIELDS
)
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_TYPE).get(name) for name in _RECEIPT_HOOKS
)


def _assert_receipt_denials() -> None:
    _assert_original_witness_carrier()
    if (
        OfflinePrivacyVetoReceipt is not _RECEIPT_TYPE
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
                _RECEIPT_HOOKS, _ORIGINAL_RECEIPT_HOOKS, strict=True,
            )
        )
        or OfflinePrivacyVetoWitness is not _WITNESS_TYPE
        or vars(_WITNESS_TYPE).get("independent_custody_verified")
        is not _ORIGINAL_WITNESS_DENIAL
        or any(
            vars(_RECEIPT_TYPE).get(name) is not descriptor
            for name, descriptor in zip(
                _RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS, strict=True,
            )
        )
    ):
        raise OfflinePrivacyVetoRejected("privacy veto receipt authority changed")


def _assert_review_denied(review: OfflinePrivacyVetoReview) -> None:
    _assert_original_review_denials()
    if type(review) is not _REVIEW_TYPE:
        raise OfflinePrivacyVetoRejected("privacy veto review acquired authority")
    original = (review.local_veto_seen, review.witness)
    for key, descriptor in zip(
        _REVIEW_DENIALS, _ORIGINAL_REVIEW_DENIALS, strict=True,
    ):
        if (
            vars(_REVIEW_TYPE).get(key) is not descriptor
            or getattr(review, key) is not False
            or review.local_veto_seen is not original[0]
            or review.witness is not original[1]
        ):
            raise OfflinePrivacyVetoRejected("privacy veto review acquired authority")
        _assert_original_review_denials()
    if any(
        vars(_REVIEW_TYPE).get(key) is not descriptor
        for key, descriptor in zip(
            _REVIEW_DENIALS, _ORIGINAL_REVIEW_DENIALS, strict=True,
        )
    ) or (review.local_veto_seen, review.witness) != original:
        raise OfflinePrivacyVetoRejected("privacy veto review changed")


def _sha(value: object) -> bool:
    # Reject oversized or truncated pseudonymous identifiers before regex.
    # A same-process malformed receipt must not reach a matching callback.
    return type(value) is str and len(value) == 64 and _SHA.fullmatch(value) is not None


def _ms(value: object) -> bool:
    return type(value) is int and 0 <= value <= _MAX_MS


def _digest(rows: tuple[tuple[object, ...], ...]) -> str:
    encoded = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(_DOMAIN + encoded).hexdigest()


def genesis_privacy_veto_witness() -> OfflinePrivacyVetoWitness:
    _assert_original_witness_carrier()
    return OfflinePrivacyVetoWitness(0, _digest(()))


def _valid_witness(witness: object) -> bool:
    _assert_original_witness_carrier()
    return (
        type(witness) is OfflinePrivacyVetoWitness
        and type(witness.count) is int
        and 0 <= witness.count <= _MAX_ROWS
        and _sha(witness.fingerprint)
    )


def _path(value: object, *, exists: bool) -> Path:
    if (
        type(value) is not type(Path("."))
        or len(str(value)) > _MAX_PATH
        or not value.is_absolute()
        or ".." in value.parts
    ):
        raise OfflinePrivacyVetoRejected("exact absolute fixture path required")
    # An ordinary parent.is_symlink() check misses symbolic GRANDPARENTS.
    # Refuse symlinked or non-directory ancestors before SQLite can create
    # or reopen a ledger through a redirected fixture path. This is not an
    # atomic defense against an attacker swapping a parent after validation.
    try:
        for parent in value.parents:
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise OfflinePrivacyVetoRejected("veto ancestor is not a real directory")
    except OSError as exc:
        raise OfflinePrivacyVetoRejected("veto ancestor unavailable") from exc
    if value.is_symlink() or (exists and not value.exists()):
        raise OfflinePrivacyVetoRejected("missing or symbolic veto ledger")
    main_exists = value.exists()
    if main_exists:
        try:
            info = value.stat(follow_symlinks=False)
        except OSError as exc:
            raise OfflinePrivacyVetoRejected("veto ledger metadata unavailable") from exc
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise OfflinePrivacyVetoRejected("veto ledger requires one regular-file link")
    # Even this disconnected privacy fixture must not open SQLite through
    # an aliased WAL/SHM/journal pathname. A safe main file cannot vouch
    # for sidecars. This lstat preflight is not atomic filesystem custody.
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = value.with_name(value.name + suffix)
        try:
            sidecar_info = sidecar.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise OfflinePrivacyVetoRejected("veto sidecar metadata unavailable") from exc
        if not main_exists:
            raise OfflinePrivacyVetoRejected("orphaned veto SQLite sidecar refused")
        if not stat.S_ISREG(sidecar_info.st_mode) or sidecar_info.st_nlink != 1:
            raise OfflinePrivacyVetoRejected("veto SQLite sidecar alias refused")
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
    _assert_original_witness_carrier()
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
    digest = _digest(tuple(rows))
    _assert_original_witness_carrier()
    return OfflinePrivacyVetoWitness(len(rows), digest)


class DisconnectedPrivacyVetoLedger:
    """Local create-only fixture database, not a consent or identity provider."""

    def __init__(self, path: Path, *, require_existing: bool = False) -> None:
        """Open or explicitly create a local veto ledger.

        On restart use require_existing=True: a missing veto DB must never
        silently become a new empty, apparently unrevoked source. This is
        a local fail-closed check, not independent backup or custody proof.
        """
        _assert_original_witness_carrier()
        if type(require_existing) is not bool:
            raise OfflinePrivacyVetoRejected("exact restart mode required")
        self._path = _path(path, exists=require_existing)
        if require_existing:
            # SQLite default connect silently creates missing files even
            # after a path check. mode=rw prevents that fallback on a race.
            conn = sqlite3.connect(
                self._path.as_uri() + "?mode=rw", uri=True,
                timeout=10, isolation_level=None,
            )
        else:
            conn = sqlite3.connect(self._path, timeout=10, isolation_level=None)
        with closing(conn) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if require_existing:
                        raise OfflinePrivacyVetoRejected(
                            "existing veto ledger is not initialized"
                        )
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
        _assert_original_witness_carrier()
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
        _assert_original_review_denials()
        source = self._path
        epoch = (retained.count, retained.fingerprint)
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                current = _inspect(conn)
                if (
                    (current.count, current.fingerprint) != epoch
                    or (retained.count, retained.fingerprint) != epoch
                ):
                    raise OfflinePrivacyVetoRejected("stale or rewritten veto evidence")
                rows = tuple(conn.execute(
                    "SELECT seq FROM synthetic_privacy_veto "
                    "WHERE owner_sha256=? AND scope_sha256=?", (owner_sha256, scope_sha256),
                ))
                if len(rows) > 1 or self._path is not source:
                    raise OfflinePrivacyVetoRejected("veto source changed during review")
                second = _inspect(conn)
                if (
                    (second.count, second.fingerprint)
                    != (current.count, current.fingerprint)
                ):
                    raise OfflinePrivacyVetoRejected("veto history changed during review")
                conn.commit()
                _assert_original_review_denials()
                result = OfflinePrivacyVetoReview(bool(rows), current)
                _assert_review_denied(result)
                if (
                    result.local_veto_seen is not bool(rows)
                    or result.witness is not current
                ):
                    raise OfflinePrivacyVetoRejected("privacy veto review changed")
                return result
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
        # Reject already-replaced False-only receipt callbacks before any
        # potentially committed local denial marker. This never grants consent.
        _assert_receipt_denials()
        epoch = (retained.count, retained.fingerprint)
        source = self._path
        with closing(self._open(read_only=False)) as conn:
            if self._path is not source:
                raise OfflinePrivacyVetoRejected("veto source changed before write")
            conn.execute("BEGIN IMMEDIATE")
            try:
                current = _inspect(conn)
                if (
                    (current.count, current.fingerprint) != epoch
                    or (retained.count, retained.fingerprint) != epoch
                ):
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
                after_epoch = (after.count, after.fingerprint)
                if (
                    self._path is not source
                    or (retained.count, retained.fingerprint) != epoch
                    or after.count != current.count + 1
                ):
                    raise OfflinePrivacyVetoRejected("veto carrier changed before commit")
                _assert_receipt_denials()
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise OfflinePrivacyVetoRejected("duplicate local veto") from exc
            except BaseException:
                conn.rollback()
                raise
        # COMMIT may already be durable even if the receipt is rejected.
        # Never retry automatically after a post-COMMIT custody exception.
        def verify_postcommit() -> None:
            try:
                _assert_receipt_denials()
            except OfflinePrivacyVetoRejected as exc:
                # SQLite COMMIT already returned: this is an ambiguous local
                # receipt outcome, not an invitation to replay the veto.
                raise OfflinePrivacyVetoRejected(
                    "veto post-COMMIT receipt authority changed; manual review required"
                ) from exc
            if (
                self._path is not source
                or type(retained) is not _WITNESS_TYPE
                or retained.count is not epoch[0]
                or retained.fingerprint is not epoch[1]
                or type(after) is not _WITNESS_TYPE
                or after.count is not after_epoch[0]
                or after.fingerprint is not after_epoch[1]
                or after.independent_custody_verified is not False
            ):
                raise OfflinePrivacyVetoRejected(
                    "veto post-COMMIT custody uncertain; manual review required"
                )

        verify_postcommit()
        receipt = _RECEIPT_TYPE(owner_sha256, scope_sha256, observed_now_ms, after)

        def verify_receipt() -> None:
            verify_postcommit()
            if (
                type(receipt) is not _RECEIPT_TYPE
                or receipt.owner_sha256 is not owner_sha256
                or receipt.scope_sha256 is not scope_sha256
                or type(receipt.recorded_at_ms) is not int
                or receipt.recorded_at_ms is not observed_now_ms
                or receipt.witness is not after
            ):
                raise OfflinePrivacyVetoRejected(
                    "veto post-COMMIT receipt uncertain; manual review required"
                )

        verify_receipt()
        for name in _RECEIPT_DENIALS:
            if getattr(receipt, name) is not False:
                raise OfflinePrivacyVetoRejected("veto receipt acquired authority")
            verify_receipt()
        return receipt
