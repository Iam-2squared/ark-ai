"""Disconnected SQLite reservation fixture for registry-bound WRITE occurrences.

This module never executes a backend or grants permission to execute one.
The supplied token, clock, registry, and issuer are NOT authenticated. A
reservation prevents fixture-level replay across restarts/processes, but does
not prove human approval, external exactly-once effects, or trusted storage.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import stat
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .contracts import Effect, OneShotAuthorization, ToolCall
from .registry import ToolRegistry

_MAX = 2**63 - 1
_OCCURRENCE = re.compile(r"occ_[0-9a-f]{64}\Z")
_TOKEN_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_REGISTRY_ID = re.compile(r"tools_[0-9a-f]{64}\Z")
_BOUND_ID = re.compile(r"bound_[0-9a-f]{64}\Z")
_REQUEST_ID = re.compile(r"act_[0-9a-f]{64}\Z")
_MAX_FIXTURE_ROWS = 10_000
_TABLE = """CREATE TABLE synthetic_occurrence_reservations(
    token_digest TEXT PRIMARY KEY NOT NULL,
    occurrence_id TEXT NOT NULL UNIQUE,
    registry_revision TEXT NOT NULL,
    bound_action_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    reserved_at_ms INTEGER NOT NULL CHECK(reserved_at_ms >= 0),
    expires_at_ms INTEGER NOT NULL CHECK(expires_at_ms >= 0)
)"""


class SyntheticReplayRejected(RuntimeError):
    """One synthetic occurrence/token cannot be reserved more than once."""


# Token IDs are private caller-supplied data. A substituted digest callback
# must not receive the token before the local reservation is even opened.
# Import-time identity is an in-process integrity guard, NOT a credential,
# signed approval, or protection against a compromised Python interpreter.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_TABLE = _TABLE
_ORIGINAL_MAX = _MAX
# The bounded synthetic ledger's capacity remains an explicit test-injection
# seam for zero/full/concurrent capacity regression fixtures. Mutating this
# budget is not evidence of authenticated authority or durable consent.
_ORIGINAL_ID_PATTERNS = (
    _OCCURRENCE, _TOKEN_DIGEST, _REGISTRY_ID, _BOUND_ID, _REQUEST_ID,
)


def _require_original_digest() -> None:
    if hashlib is not _ORIGINAL_HASHLIB or hashlib.sha256 is not _ORIGINAL_SHA256:
        raise SyntheticReplayRejected(
            "synthetic occurrence digest implementation changed before token hashing"
        )


def _require_original_protocol() -> None:
    """Pin fixture schema, timestamp bound and IDs before reading tokens.

    These process-local checks do not authenticate approval, filesystem
    ownership, or any external action.
    """
    _require_original_digest()
    if (
        _TABLE is not _ORIGINAL_TABLE
        or type(_MAX) is not int or _MAX != _ORIGINAL_MAX
        or any(
            current is not original
            for current, original in zip(
                (_OCCURRENCE, _TOKEN_DIGEST, _REGISTRY_ID, _BOUND_ID, _REQUEST_ID),
                _ORIGINAL_ID_PATTERNS, strict=True,
            )
        )
    ):
        raise SyntheticReplayRejected("synthetic occurrence protocol changed")


@dataclass(frozen=True, slots=True)
class SyntheticReservationReceipt:
    occurrence_id: str
    registry_revision: str
    bound_action_id: str
    request_id: str
    reserved_at_ms: int

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def outcome_known(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


# Preserve the exact inert receipt class even if a synthetic fault fixture
# replaces the exported constructor after the SQLite reservation has committed.
_RECEIPT_CLASS = SyntheticReservationReceipt
_RECEIPT_DENIALS = ("dispatch_authorized", "outcome_known", "automatic_replay_authorized")
_ORIGINAL_RECEIPT_DENIALS = tuple(
    vars(_RECEIPT_CLASS)[name] for name in _RECEIPT_DENIALS
)
# A frozen dataclass remains patchable at class level. Reject executable slot
# descriptors and constructor/getter hooks before the FIRST returned field
# lookup, including a substituted False-only receipt after durable COMMIT.
_RECEIPT_FIELDS = (
    "occurrence_id", "registry_revision", "bound_action_id",
    "request_id", "reserved_at_ms",
)
_RECEIPT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RECEIPT_FIELDS = tuple(
    vars(_RECEIPT_CLASS)[name] for name in _RECEIPT_FIELDS
)
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_CLASS).get(name) for name in _RECEIPT_HOOKS
)


def _assert_receipt_denials() -> None:
    """Require the original inert receipt class before accessing its slots."""
    if (
        SyntheticReservationReceipt is not _RECEIPT_CLASS
        or any(
            vars(_RECEIPT_CLASS).get(name) is not original
            for names, originals in (
                (_RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS),
                (_RECEIPT_FIELDS, _ORIGINAL_RECEIPT_FIELDS),
                (_RECEIPT_HOOKS, _ORIGINAL_RECEIPT_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticReplayRejected("synthetic receipt authority descriptor changed")



def _objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    # One table and exactly two SQLite-generated uniqueness indexes.
    # Refuse oversized/foreign catalog entries before Python receives DDL.
    budget = conn.execute(
        "SELECT COUNT(*),COALESCE(SUM(length(CAST(sql AS BLOB))),0) "
        "FROM sqlite_master"
    ).fetchone()
    if (
        type(budget) is not tuple or len(budget) != 2
        or type(budget[0]) is not int or budget[0] != 3
        or type(budget[1]) is not int or not 0 <= budget[1] <= 8_192
    ):
        raise SyntheticReplayRejected("synthetic reservation schema changed")
    return tuple(
        tuple(row) for row in conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "ORDER BY type,name LIMIT 3"
        )
    )


def _validate(conn: sqlite3.Connection) -> None:
    _require_original_protocol()
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise SyntheticReplayRejected("synthetic reservation schema version changed")
    # The SQLite connection context manager controls transactions, not handle lifetime.
    # Close the disposable DDL oracle on success and every fail-closed rejection.
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.execute(_TABLE)
        if _objects(conn) != _objects(expected):
            raise SyntheticReplayRejected("synthetic reservation schema changed")
    if conn.execute("PRAGMA quick_check").fetchmany(2) != [("ok",)]:
        raise SyntheticReplayRejected("synthetic reservation storage failed quick_check")

    # Admit only bounded, exact-storage-class rows before Python hydration.
    # The later regex/timestamp replay remains authoritative for row identity.
    budget = conn.execute(
        "SELECT COUNT(*),COALESCE(SUM(CASE WHEN "
        "typeof(token_digest)='text' AND length(CAST(token_digest AS BLOB))=64 "
        "AND typeof(occurrence_id)='text' "
        "AND length(CAST(occurrence_id AS BLOB))=68 "
        "AND typeof(registry_revision)='text' "
        "AND length(CAST(registry_revision AS BLOB))=70 "
        "AND typeof(bound_action_id)='text' "
        "AND length(CAST(bound_action_id AS BLOB))=70 "
        "AND typeof(request_id)='text' "
        "AND length(CAST(request_id AS BLOB))=68 "
        "AND typeof(reserved_at_ms)='integer' "
        "AND typeof(expires_at_ms)='integer' "
        "AND reserved_at_ms >= 0 AND reserved_at_ms < expires_at_ms "
        "AND expires_at_ms <= ? THEN 0 ELSE 1 END),0) "
        "FROM synthetic_occurrence_reservations",
        (_MAX,),
    ).fetchone()
    if (
        type(budget) is not tuple or len(budget) != 2
        or type(budget[0]) is not int
        or not 0 <= budget[0] <= _MAX_FIXTURE_ROWS
        or type(budget[1]) is not int or budget[1] != 0
    ):
        raise SyntheticReplayRejected("synthetic reservation row integrity failed (SQL preflight)")

    # SQLite's quick_check verifies storage and CHECK constraints, but it
    # cannot certify the canonical identity and time relationships in rows.
    # Review a bounded fixture ledger on every open, read and reservation.
    rows = conn.execute(
        """SELECT token_digest, occurrence_id, registry_revision,
                  bound_action_id, request_id, reserved_at_ms, expires_at_ms
           FROM synthetic_occurrence_reservations"""
    )
    for index, row in enumerate(rows):
        if index >= _MAX_FIXTURE_ROWS:
            raise SyntheticReplayRejected("synthetic reservation review budget exceeded")
        token, occurrence, revision, bound, request, reserved, expires = row
        if (
            type(token) is not str or not _TOKEN_DIGEST.fullmatch(token)
            or type(occurrence) is not str or not _OCCURRENCE.fullmatch(occurrence)
            or type(revision) is not str or not _REGISTRY_ID.fullmatch(revision)
            or type(bound) is not str or not _BOUND_ID.fullmatch(bound)
            or type(request) is not str or not _REQUEST_ID.fullmatch(request)
            or type(reserved) is not int or type(expires) is not int
            or not 0 <= reserved < expires <= _MAX
        ):
            raise SyntheticReplayRejected("synthetic reservation row integrity failed")


def _require_safe_occurrence_path(path: object, *, create: bool) -> Path:
    """Reject symlinked/nonregular local reservation ledger paths pre-open.

    This repeated local lstat preflight cannot defeat concurrent path renames
    by a filesystem owner. It conveys neither trust nor execution authority.
    """
    if type(path) is not type(Path()) or ".." in path.parts:
        raise SyntheticReplayRejected("synthetic occurrence path alias refused")
    target = path if path.is_absolute() else path.absolute()
    try:
        for ancestor in target.parents:
            try:
                meta = ancestor.lstat()
            except FileNotFoundError:
                raise SyntheticReplayRejected(
                    "synthetic occurrence ancestor unavailable"
                ) from None
            if not stat.S_ISDIR(meta.st_mode) or stat.S_ISLNK(meta.st_mode):
                raise SyntheticReplayRejected("synthetic occurrence ancestor unsafe")
        main_absent = False
        try:
            meta = target.lstat()
        except FileNotFoundError:
            main_absent = True
            if not create:
                raise sqlite3.OperationalError(
                    "synthetic occurrence storage missing"
                ) from None
        else:
            if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1:
                raise SyntheticReplayRejected("synthetic occurrence ledger path unsafe")
        # A legitimate main DB can still be redirected through an aliased
        # SQLite journal or WAL file. Refuse unsafe -wal/-shm/-journal entries
        # before SQLite reads or writes; do not adopt any orphaned journal
        # when creating a new disconnected fixture ledger.
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = target.with_name(target.name + suffix)
            try:
                sidecar_info = sidecar.lstat()
            except FileNotFoundError:
                continue
            if main_absent:
                raise SyntheticReplayRejected("orphaned occurrence SQLite sidecar refused")
            if not stat.S_ISREG(sidecar_info.st_mode) or sidecar_info.st_nlink != 1:
                raise SyntheticReplayRejected("occurrence SQLite sidecar alias refused")
    except OSError as exc:
        raise SyntheticReplayRejected("synthetic occurrence path cannot be verified") from exc
    return path


class SyntheticOccurrenceStore:
    """No-execution fixture ledger; not a real PermissionGate or token issuer."""

    def __init__(self, path: Path) -> None:
        _require_original_protocol()
        if not isinstance(path, Path):
            raise TypeError("synthetic ledger path must be a pathlib.Path")
        self._path = path
        with closing(self._connect(create=True)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if conn.execute(
                        "SELECT 1 FROM sqlite_master LIMIT 1"
                    ).fetchone() is not None:
                        raise SyntheticReplayRejected(
                            "synthetic ledger is nonempty without a schema version"
                        )
                    conn.execute(_TABLE)
                    conn.execute("PRAGMA user_version=1")
                _validate(conn)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _connect(
        self, *, create: bool = False, pinned_path: Path | None = None,
    ) -> sqlite3.Connection:
        source = self._path if pinned_path is None else pinned_path
        _require_safe_occurrence_path(source, create=create)
        if create:
            # Only explicit fixture initialization may create storage.
            return sqlite3.connect(source, timeout=10, isolation_level=None)
        # A stale store must not recreate a deleted/moved reservation ledger.
        # URI mode=rw also preserves literal special path characters.
        uri = source.resolve().as_uri() + "?mode=rw"
        return sqlite3.connect(uri, uri=True, timeout=10, isolation_level=None)

    def reserve_synthetic(
        self,
        registry: ToolRegistry,
        call: ToolCall,
        token: OneShotAuthorization,
        *,
        occurrence_id: str,
        now_ms: int,
    ) -> SyntheticReservationReceipt:
        """Commit a synthetic reservation before returning an inert receipt.

        This method does not verify consent, real issuer signatures, or clock
        trustworthiness. It must never be used to dispatch a real WRITE.
        """
        if (
            type(registry) is not ToolRegistry
            or type(call) is not ToolCall
            or type(token) is not OneShotAuthorization
        ):
            raise SyntheticReplayRejected("synthetic reservation requires exact inputs")
        if type(now_ms) is not int or not 0 <= now_ms <= _MAX:
            raise SyntheticReplayRejected("invalid synthetic reservation timestamp")
        if type(occurrence_id) is not str or not _OCCURRENCE.fullmatch(occurrence_id):
            raise SyntheticReplayRejected("invalid synthetic occurrence identity")
        # Denial properties are import-time invariants, not callbacks that a
        # registry/SQLite fixture may replace with even an always-False getter.
        _require_original_protocol()
        _assert_receipt_denials()
        # Pin the initialized source before any caller-supplied registry work.
        # A reflected equal-value Path replacement is a different review epoch.
        path_epoch = self._path
        if not isinstance(path_epoch, Path):
            raise SyntheticReplayRejected("synthetic occurrence source must be a Path")
        # Auth token fields must be pinned *before* the registry callback.
        # Otherwise a reflected token swap during first bind becomes the
        # supposed original epoch and can reserve a different token.
        token_epoch = (token.token_id, token.request_id, token.expires_at_ms)
        # Capture the original WRITE subject before the first registry callback,
        # not after its return. Reflection can retarget an otherwise frozen
        # ToolCall or token while the ledger is about to be reserved.
        arguments_epoch = call.arguments
        call_epoch = (
            call.tool, call.capability, call.scope, call.request_id,
            call.arguments_sha256,
        )

        def assert_input_epoch() -> None:
            _require_original_protocol()
            _assert_receipt_denials()
            # Preserve established fail-closed provenance diagnostics, so
            # source vs token changes remain distinguishable in durable tests.
            if self._path is not path_epoch:
                raise SyntheticReplayRejected(
                    "synthetic occurrence source changed during reserve"
                )
            try:
                if (token.token_id, token.request_id, token.expires_at_ms) != token_epoch:
                    raise SyntheticReplayRejected(
                        "synthetic token changed during reserve"
                    )
                stable = (
                    call.arguments is arguments_epoch
                    and (
                        call.tool, call.capability, call.scope,
                        call.request_id, call.arguments_sha256,
                    ) == call_epoch
                )
            except (TypeError, ValueError, AttributeError) as exc:
                raise SyntheticReplayRejected(
                    "synthetic occurrence input changed during reserve"
                ) from exc
            if not stable:
                raise SyntheticReplayRejected(
                    "synthetic occurrence input changed during reserve"
                )

        try:
            first = registry.bind(call)
            assert_input_epoch()
            if first.call is not call:
                raise SyntheticReplayRejected(
                    "synthetic registry returned a different action subject"
                )
            if first.registration.effect is not Effect.WRITE:
                raise SyntheticReplayRejected("only synthetic WRITE occurrences can reserve")
            if token.request_id != first.call.request_id or token.expires_at_ms <= now_ms:
                raise SyntheticReplayRejected("synthetic token is expired or mismatched")
            token_digest = hashlib.sha256(
                ("ARK-synthetic-v1\0" + token.token_id).encode("utf-8")
            ).hexdigest()
            # Hashing may be substituted by a deterministic fault fixture;
            # never reserve a digest computed across two token epochs.
            assert_input_epoch()
        except (TypeError, ValueError, AttributeError, KeyError) as exc:
            raise SyntheticReplayRejected("synthetic registry binding failed") from exc

        assert_input_epoch()
        with closing(self._connect(pinned_path=path_epoch)) as conn:
            assert_input_epoch()
            conn.execute("BEGIN IMMEDIATE")
            assert_input_epoch()
            try:
                _validate(conn)
                assert_input_epoch()
                # A committed fixture reservation is a lower bound on later
                # caller-supplied times. This is not a trusted clock: an
                # attacker replacing the whole DB can also reset this bound.
                latest = conn.execute(
                    "SELECT MAX(reserved_at_ms) FROM synthetic_occurrence_reservations"
                ).fetchone()[0]
                assert_input_epoch()
                if latest is not None and now_ms < latest:
                    raise SyntheticReplayRejected(
                        "synthetic reservation clock regressed"
                    )
                # The read-side validator permits exactly _MAX_FIXTURE_ROWS
                # entries, but adding one more would strand the ledger in
                # an unreadable state on the next open. Check capacity under
                # the SAME SQLite writer transaction as the INSERT. Concurrent
                # processes cannot both cross the bound.
                existing_rows = conn.execute(
                    "SELECT COUNT(*) FROM synthetic_occurrence_reservations"
                ).fetchone()[0]
                assert_input_epoch()
                if (
                    type(existing_rows) is not int
                    or existing_rows < 0
                    or existing_rows >= _MAX_FIXTURE_ROWS
                ):
                    raise SyntheticReplayRejected(
                        "synthetic reservation ledger capacity exhausted"
                    )
                again = registry.bind(call)
                assert_input_epoch()
                if (
                    again.call is not call
                    or again.bound_action_id != first.bound_action_id
                    or again.registry_revision != first.registry_revision
                    or again.registration is not first.registration
                    or again.call is not first.call
                    or (token.token_id, token.request_id, token.expires_at_ms)
                    != token_epoch
                    or token.request_id != again.call.request_id
                ):
                    raise SyntheticReplayRejected(
                        "synthetic action or token identity changed before reserve"
                    )
                try:
                    conn.execute(
                        """INSERT INTO synthetic_occurrence_reservations(
                            token_digest, occurrence_id, registry_revision,
                            bound_action_id, request_id, reserved_at_ms, expires_at_ms
                        ) VALUES (?,?,?,?,?,?,?)""",
                        (
                            token_digest, occurrence_id, again.registry_revision,
                            again.bound_action_id, again.call.request_id,
                            now_ms, token.expires_at_ms,
                        ),
                    )
                except sqlite3.IntegrityError as exc:
                    raise SyntheticReplayRejected(
                        "synthetic token or occurrence was already reserved"
                    ) from exc
                assert_input_epoch()
                conn.commit()
                assert_input_epoch()
            except BaseException:
                conn.rollback()
                raise
        assert_input_epoch()
        # Constructing a receipt is a reflective callback after durable COMMIT.
        # Reject forged/equal-text-retargeted results and changed inputs without
        # pretending that the committed one-shot reservation was rolled back.
        receipt_fields = (
            occurrence_id, first.registry_revision, first.bound_action_id,
            token_epoch[1], now_ms,
        )
        receipt = SyntheticReservationReceipt(*receipt_fields)
        assert_input_epoch()
        if (
            type(receipt) is not _RECEIPT_CLASS
            or any(
                getattr(receipt, name) is not original
                for name, original in zip((
                    "occurrence_id", "registry_revision", "bound_action_id",
                    "request_id", "reserved_at_ms",
                ), receipt_fields, strict=True)
            )
            or first.registry_revision is not receipt_fields[1]
            or first.bound_action_id is not receipt_fields[2]
        ):
            raise SyntheticReplayRejected(
                "synthetic receipt identity changed after reservation commit"
            )
        # A frozen receipt can still expose patched class properties. Never
        # hand a caller an apparently authorized synthetic reservation. Check
        # after each getter because any getter may alter an earlier descriptor
        # or mutate a frozen result by reflection after the SQLite COMMIT.
        for name in _RECEIPT_DENIALS:
            if getattr(receipt, name) is not False:
                raise SyntheticReplayRejected("synthetic receipt acquired authority")
            assert_input_epoch()
            if (
                type(receipt) is not _RECEIPT_CLASS
                or any(
                    getattr(receipt, field) is not original
                    for field, original in zip((
                        "occurrence_id", "registry_revision", "bound_action_id",
                        "request_id", "reserved_at_ms",
                    ), receipt_fields, strict=True)
                )
            ):
                raise SyntheticReplayRejected(
                    "synthetic receipt identity changed after authority review"
                )
        return receipt

    def count_synthetic(self) -> int:
        """Read-only count; missing DB is never created as a side effect."""
        _require_original_protocol()
        path_epoch = self._path
        if not isinstance(path_epoch, Path):
            raise SyntheticReplayRejected("synthetic occurrence source must be a Path")

        def assert_source_epoch() -> None:
            if self._path is not path_epoch:
                raise SyntheticReplayRejected(
                    "synthetic occurrence source changed during count"
                )

        # Path resolution, URI construction, SQLite open and BEGIN are
        # separate reentrant boundaries. Reject an equal-path replacement
        # before querying a possibly unrelated private reservation ledger.
        assert_source_epoch()
        _require_safe_occurrence_path(path_epoch, create=False)
        assert_source_epoch()
        resolved = path_epoch.resolve()
        assert_source_epoch()
        uri = resolved.as_uri() + "?mode=ro"
        assert_source_epoch()
        with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
            assert_source_epoch()
            conn.execute("BEGIN")
            assert_source_epoch()
            try:
                _validate(conn)
                assert_source_epoch()
                count = conn.execute(
                    "SELECT COUNT(*) FROM synthetic_occurrence_reservations"
                ).fetchone()[0]
                assert_source_epoch()
                conn.commit()
                assert_source_epoch()
                return count
            except BaseException:
                conn.rollback()
                raise
