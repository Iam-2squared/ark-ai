"""Content-minimized, durable synthetic proactive preparation deduplication.

Only local fixture 'prepared' markers are emitted. Caller clocks and scopes
are not authenticated. No real notifications, model calls or actions happen.
This is NOT a scheduler service, an approval issuer or action permission.
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

_MAX = 2**63 - 1
_MAX_PREPARATIONS = 10_000
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_TRIGGER = re.compile(r"trigger_[0-9a-f]{64}\Z")
_TABLE = """CREATE TABLE synthetic_prepared_triggers(
    trigger_id TEXT PRIMARY KEY,
    scope_digest TEXT NOT NULL,
    policy_digest TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    observation_digest TEXT NOT NULL,
    observed_at_ms INTEGER NOT NULL,
    prepared_at_ms INTEGER NOT NULL
)"""


class SyntheticTriggerRejected(RuntimeError):
    """The fixture refuses a duplicate, over-budget or invalid preparation."""


def _hash(label: str, values: object) -> str:
    encoded = json.dumps(
        values, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(label.encode("utf-8") + b"\0" + encoded).hexdigest()


def _text(name: str, value: object) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{name} must be a nonempty exact string")
    if len(value) > 512:
        raise ValueError(f"{name} exceeds policy string budget")
    # The persisted trigger digest serializes policy text in UTF-8. Treat a
    # 512-character multibyte label as over-budget and reject unpaired
    # surrogates before hashing, SQLite access or scheduler decisions.
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise ValueError(f"{name} must be valid UTF-8") from exc
    if size > 512:
        raise ValueError(f"{name} exceeds policy string budget")


def _int(name: str, value: object, *, minimum: int = 0) -> None:
    if type(value) is not int or not minimum <= value <= _MAX:
        raise ValueError(f"{name} must be an exact bounded integer")


@dataclass(frozen=True, slots=True)
class SyntheticTriggerPolicy:
    owner: str
    namespace: str
    definition_id: str
    revision: int
    policy_revision: str
    minimum_interval_ms: int
    rolling_window_ms: int
    max_preparations_per_window: int

    def __post_init__(self) -> None:
        # Validation hooks can be reentrant in offline fixture reviews. Pin
        # the entire original policy before the first hook, and check after
        # EACH field; a later field must not hide temporary identity drift.
        field_names = (
            "owner", "namespace", "definition_id", "revision",
            "policy_revision", "minimum_interval_ms", "rolling_window_ms",
            "max_preparations_per_window",
        )
        original = tuple(getattr(self, name) for name in field_names)

        def assert_policy_epoch() -> None:
            if any(
                getattr(self, name) is not carrier
                for name, carrier in zip(field_names, original, strict=True)
            ):
                raise ValueError("synthetic trigger policy changed during validation")

        for name in ("owner", "namespace", "definition_id", "policy_revision"):
            _text(name, getattr(self, name))
            assert_policy_epoch()
        for name in ("revision", "minimum_interval_ms", "rolling_window_ms",
                     "max_preparations_per_window"):
            _int(name, getattr(self, name), minimum=1)
            assert_policy_epoch()

    def identity(self) -> tuple[object, ...]:
        original = (
            self.owner, self.namespace, self.definition_id, self.revision,
            self.policy_revision, self.minimum_interval_ms,
            self.rolling_window_ms, self.max_preparations_per_window,
        )
        self.__post_init__()
        if any(
            now is not before for now, before in zip(
                (
                    self.owner, self.namespace, self.definition_id, self.revision,
                    self.policy_revision, self.minimum_interval_ms,
                    self.rolling_window_ms, self.max_preparations_per_window,
                ),
                original, strict=True,
            )
        ):
            raise ValueError("synthetic trigger policy changed during identity review")
        return original


# A frozen policy instance is not protected against class-level replacement of
# field slots, the identity validator, or attribute lookup hooks. Pin the exact
# import-original class contract before the first private policy field read.
_POLICY_TYPE = SyntheticTriggerPolicy
_POLICY_FIELDS = (
    "owner", "namespace", "definition_id", "revision", "policy_revision",
    "minimum_interval_ms", "rolling_window_ms", "max_preparations_per_window",
)
_POLICY_METHODS = (
    "identity", "__post_init__", "__init__", "__new__",
    "__getattribute__", "__getattr__",
)
_ORIGINAL_POLICY_FIELDS = tuple(
    vars(_POLICY_TYPE)[name] for name in _POLICY_FIELDS
)
_ORIGINAL_POLICY_METHODS = tuple(
    vars(_POLICY_TYPE).get(name) for name in _POLICY_METHODS
)


def _require_original_policy_contract() -> None:
    if (
        SyntheticTriggerPolicy is not _POLICY_TYPE
        or any(
            vars(_POLICY_TYPE).get(name) is not original
            for names, originals in (
                (_POLICY_FIELDS, _ORIGINAL_POLICY_FIELDS),
                (_POLICY_METHODS, _ORIGINAL_POLICY_METHODS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticTriggerRejected("synthetic trigger policy contract changed")


@dataclass(frozen=True, slots=True)
class SyntheticTriggerReceipt:
    trigger_id: str
    prepared_at_ms: int

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


# This marker is a local deduplication receipt, never a permission or outcome.
# Its class and False-only descriptors must be the ORIGINAL declarations;
# replacing one with a new property returning False is also authority drift.
_RECEIPT_TYPE = SyntheticTriggerReceipt
_RECEIPT_DENIALS = (
    "notification_authorized", "dispatch_authorized",
    "automatic_replay_authorized",
)
_ORIGINAL_RECEIPT_DENIALS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_DENIALS
)
# A frozen slotted receipt still permits class-level replacement of a field,
# constructor or lookup hook. Check the original class dictionary BEFORE any
# post-COMMIT constructor or field access; a later False getter cannot undo an
# injected side effect.
_RECEIPT_FIELDS = ("trigger_id", "prepared_at_ms")
_RECEIPT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RECEIPT_FIELDS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_FIELDS
)
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_TYPE).get(name) for name in _RECEIPT_HOOKS
)


def _require_original_receipt_authority() -> None:
    if (
        SyntheticTriggerReceipt is not _RECEIPT_TYPE
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for names, originals in (
                (_RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS),
                (_RECEIPT_FIELDS, _ORIGINAL_RECEIPT_FIELDS),
                (_RECEIPT_HOOKS, _ORIGINAL_RECEIPT_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticTriggerRejected("trigger receipt authority epoch changed")


def _objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    # A trigger fixture has exactly one table and its PRIMARY KEY index.
    # Admit catalog size in SQLite before hydrating potentially hostile DDL.
    budget = conn.execute(
        "SELECT COUNT(*),COALESCE(SUM(length(CAST(sql AS BLOB))),0) "
        "FROM sqlite_master"
    ).fetchone()
    if (
        type(budget) is not tuple or len(budget) != 2
        or type(budget[0]) is not int or budget[0] != 2
        or type(budget[1]) is not int or not 0 <= budget[1] <= 4_096
    ):
        raise SyntheticTriggerRejected("trigger fixture schema changed")
    return tuple(
        tuple(row) for row in conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "ORDER BY type,name LIMIT 2"
        )
    )


def _validate(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise SyntheticTriggerRejected("trigger fixture schema version changed")
    # The SQLite connection context manager does not close disposable handles.
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.execute(_TABLE)
        if _objects(conn) != _objects(expected):
            raise SyntheticTriggerRejected("trigger fixture schema changed")
    # Only two diagnostics are needed to reject anything but one exact "ok".
    quick = conn.execute("PRAGMA quick_check").fetchmany(2)
    if len(quick) != 1 or tuple(quick[0]) != ("ok",):
        raise SyntheticTriggerRejected("trigger fixture integrity failed")
    rows = conn.execute(
        """SELECT trigger_id,scope_digest,policy_digest,source_digest,
                  observation_digest,observed_at_ms,prepared_at_ms
           FROM synthetic_prepared_triggers"""
    )
    for index, row in enumerate(rows):
        if index >= _MAX_PREPARATIONS:
            raise SyntheticTriggerRejected("trigger fixture review budget exceeded")
        identity, scope, policy, source, observation, observed, prepared = row
        if (
            type(identity) is not str or not _TRIGGER.fullmatch(identity)
            or any(
                type(field) is not str or not _HEX.fullmatch(field)
                for field in (scope, policy, source, observation)
            )
            or type(observed) is not int or type(prepared) is not int
            or not 0 <= observed <= prepared <= _MAX
        ):
            raise SyntheticTriggerRejected("persisted trigger row integrity failed")
        # The primary key is a binding over all four persisted digests,
        # not merely a syntactically valid arbitrary trigger identifier.
        if identity != "trigger_" + _hash(
            "ARK-trigger-occurrence-v1",
            (scope, policy, source, observation),
        ):
            raise SyntheticTriggerRejected(
                "persisted trigger identity does not match bound digests"
            )


_SQLITE_SIDECARS = ("-wal", "-shm", "-journal")


def _refuse_aliased_proactive_path(path: Path) -> None:
    """Preflight the literal SQLite path; never follow a known local alias.

    This read-only lstat fence does not defeat an attacker racing path swaps
    between checks and SQLite open. No directory, file or sidecar is removed.
    A missing main file is still handled by SQLite as before on read/write.
    """
    if type(path) is not type(Path(".")) or ".." in path.parts:
        raise SyntheticTriggerRejected("proactive ledger path changed")
    target = path if path.is_absolute() else path.absolute()
    try:
        for ancestor in target.parents:
            parent = ancestor.lstat()
            if not stat.S_ISDIR(parent.st_mode) or stat.S_ISLNK(parent.st_mode):
                raise SyntheticTriggerRejected("unsafe proactive parent path")
        try:
            main = target.lstat()
        except FileNotFoundError:
            absent = True
        else:
            absent = False
            if not stat.S_ISREG(main.st_mode) or main.st_nlink != 1:
                raise SyntheticTriggerRejected("unsafe proactive SQLite file")
        for suffix in _SQLITE_SIDECARS:
            sidecar = target.with_name(target.name + suffix)
            try:
                info = sidecar.lstat()
            except FileNotFoundError:
                continue
            if absent or not stat.S_ISREG(info.st_mode):
                raise SyntheticTriggerRejected("unsafe proactive SQLite sidecar")
            if info.st_nlink == 0:
                # SQLite can unlink a short-lived rollback journal between
                # pathname lookup and lstat's inode snapshot. Only this
                # already-unlinked *regular* inode may be rechecked once.
                # Symlinks, hardlinks and special files are never retried.
                try:
                    info = sidecar.lstat()
                except FileNotFoundError:
                    continue
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise SyntheticTriggerRejected("unsafe proactive SQLite sidecar")
    except OSError as exc:
        raise SyntheticTriggerRejected("proactive SQLite path unavailable") from exc


class SyntheticProactiveLedger:
    """SQLite CAS-like admission for offline preparations, no execution."""

    def __init__(self, path: Path) -> None:
        # Path subclasses may execute arbitrary __fspath__/stat hooks during
        # SQLite open. Reject before opening or creating a local trigger store.
        if type(path) is not type(Path(".")):
            raise TypeError("synthetic proactive path must be an exact local Path")
        _refuse_aliased_proactive_path(path)
        self.path = path
        with closing(sqlite3.connect(path, timeout=10, isolation_level=None)) as conn:
            _refuse_aliased_proactive_path(path)
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    # The unversioned bootstrap must admit an *empty* catalog
                    # without invoking the versioned, exactly-two-object
                    # schema oracle. Even one foreign object remains denied,
                    # and no stored DDL is hydrated before the rejection.
                    if conn.execute(
                        "SELECT 1 FROM sqlite_master LIMIT 1"
                    ).fetchone() is not None:
                        raise SyntheticTriggerRejected(
                            "unversioned trigger fixture is not empty"
                        )
                    conn.execute(_TABLE)
                    conn.execute("PRAGMA user_version=1")
                _validate(conn)
                _refuse_aliased_proactive_path(path)
                if self.path is not path:
                    raise SyntheticTriggerRejected(
                        "proactive ledger path changed during initialization"
                    )
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def prepare(
        self, policy: SyntheticTriggerPolicy, *,
        source_digest: str, observation_digest: str,
        observed_at_ms: int, now_ms: int,
        retained: object | None = None,
    ) -> SyntheticTriggerReceipt:
        """Persist a content-free preparation marker, never an action."""
        if type(policy) is not SyntheticTriggerPolicy:
            raise SyntheticTriggerRejected("exact trigger policy required")
        _require_original_policy_contract()
        _require_original_receipt_authority()
        if (
            type(source_digest) is not str or not _HEX.fullmatch(source_digest)
            or type(observation_digest) is not str
            or not _HEX.fullmatch(observation_digest)
        ):
            raise SyntheticTriggerRejected("canonical source/observation hashes required")
        _int("observed_at_ms", observed_at_ms)
        _int("now_ms", now_ms)
        if observed_at_ms > now_ms:
            raise SyntheticTriggerRejected("future observation cannot prepare")
        # Retain the caller's earlier witness in an independent location.
        # A witness reconstructed from this same potentially altered SQLite
        # file offers no rollback protection.
        from .proactive_synthetic_continuity_review import (
            _ROWS,
            SyntheticTriggerWitness,
            _digest,
            assert_proactive_history_continues,
        )

        # The independent retained-witness validation is a reentrant
        # callback. Bind the original policy and database BEFORE invoking it:
        # otherwise a mutated, equally valid policy/path becomes the baseline
        # of a newly persisted synthetic preparation.
        ledger_path = self.path
        if type(ledger_path) is not type(Path(".")):
            raise SyntheticTriggerRejected("proactive ledger path changed")
        # Policy fields are immutable values but their carriers can be swapped
        # reflectively during digest / SQLite callbacks. Preserve the exact
        # field objects before the first policy validation callback.
        policy_names = (
            "owner", "namespace", "definition_id", "revision",
            "policy_revision", "minimum_interval_ms", "rolling_window_ms",
            "max_preparations_per_window",
        )
        policy_carriers = tuple(getattr(policy, name) for name in policy_names)
        pinned = policy.identity()

        def assert_policy_epoch(stage: str) -> None:
            _require_original_policy_contract()
            if (
                self.path is not ledger_path
                or any(
                    getattr(policy, name) is not carrier
                    for name, carrier in zip(policy_names, policy_carriers, strict=True)
                )
            ):
                raise SyntheticTriggerRejected(
                    f"policy or ledger path changed {stage}"
                )
            if policy.identity() != pinned or self.path is not ledger_path or any(
                getattr(policy, name) is not carrier
                for name, carrier in zip(policy_names, policy_carriers, strict=True)
            ):
                raise SyntheticTriggerRejected(
                    f"policy or ledger path changed {stage}"
                )

        assert_policy_epoch("before preparation")
        retained_epoch = None
        retained_rows_carrier = None
        if retained is not None:
            if type(retained) is not SyntheticTriggerWitness:
                raise SyntheticTriggerRejected("exact retained proactive witness required")
            retained_rows_carrier = retained.row_hashes
            retained_epoch = (retained.row_hashes, retained.digest)
            retained.assert_integrity()
            if (
                retained.row_hashes is not retained_rows_carrier
                or (retained.row_hashes, retained.digest) != retained_epoch
            ):
                raise SyntheticTriggerRejected("retained proactive witness changed")
        assert_policy_epoch("before preparation")

        def assert_digest_epoch() -> None:
            # Each synthetic digest is a potential reentrant callback. A
            # later digest must not be able to restore an earlier policy or
            # retained-history mutation before the SQLite write fence.
            assert_policy_epoch("during trigger digest")
            if retained_epoch is not None and (
                retained.row_hashes is not retained_rows_carrier
                or (retained.row_hashes, retained.digest) != retained_epoch
            ):
                raise SyntheticTriggerRejected(
                    "retained proactive witness changed during trigger digest"
                )

        scope = _hash("ARK-trigger-scope-v1", pinned[:4])
        assert_digest_epoch()
        policy_hash = _hash("ARK-trigger-policy-v1", pinned)
        assert_digest_epoch()
        trigger = "trigger_" + _hash(
            "ARK-trigger-occurrence-v1",
            (scope, policy_hash, source_digest, observation_digest),
        )
        assert_digest_epoch()
        _refuse_aliased_proactive_path(ledger_path)
        resolved = ledger_path.resolve()
        if self.path is not ledger_path:
            raise SyntheticTriggerRejected("proactive ledger path changed before opening")
        uri = resolved.as_uri() + "?mode=rw"
        if self.path is not ledger_path:
            raise SyntheticTriggerRejected("proactive ledger path changed before opening")
        with closing(sqlite3.connect(
            uri, uri=True, timeout=10, isolation_level=None,
        )) as conn:
            # Reject drift introduced during handle creation before taking a
            # writer slot or making the first persistent schema read.
            if self.path is not ledger_path:
                raise SyntheticTriggerRejected("proactive ledger path changed before opening")
            _refuse_aliased_proactive_path(ledger_path)
            conn.execute("BEGIN IMMEDIATE")
            try:
                if self.path is not ledger_path:
                    raise SyntheticTriggerRejected("proactive ledger path changed")
                _validate(conn)
                if retained_epoch is not None:
                    if (
                        retained.row_hashes is not retained_rows_carrier
                        or (retained.row_hashes, retained.digest) != retained_epoch
                    ):
                        raise SyntheticTriggerRejected("retained proactive witness changed")
                    # Evaluate the historical fence INSIDE the same write
                    # transaction that admits a new synthetic trigger.
                    hashes = tuple(sorted(
                        _digest("ARK-trigger-row-v1", row)
                        for row in conn.execute(_ROWS)
                    ))
                    current = SyntheticTriggerWitness(
                        hashes, "synthetic_triggers_" + _digest(
                            "ARK-trigger-witness-v1", hashes,
                        ),
                    )
                    assert_proactive_history_continues(retained, current)
                    if (
                        retained.row_hashes is not retained_rows_carrier
                        or (retained.row_hashes, retained.digest) != retained_epoch
                    ):
                        raise SyntheticTriggerRejected("retained proactive witness changed")
                assert_policy_epoch("before preparation")
                recent = conn.execute(
                    """SELECT prepared_at_ms FROM synthetic_prepared_triggers
                       WHERE scope_digest=? AND policy_digest=?
                       ORDER BY prepared_at_ms DESC""",
                    (scope, policy_hash),
                ).fetchall()
                if recent and now_ms < recent[0][0]:
                    raise SyntheticTriggerRejected("trigger clock regressed")
                if recent and now_ms - recent[0][0] < policy.minimum_interval_ms:
                    raise SyntheticTriggerRejected("minimum preparation interval")
                count = sum(
                    at > now_ms - policy.rolling_window_ms for (at,) in recent
                )
                if count >= policy.max_preparations_per_window:
                    raise SyntheticTriggerRejected("rolling preparation budget")
                # A valid fixture must remain readable on its next open.
                # Count within this SAME BEGIN IMMEDIATE transaction as the
                # insertion, so competing writers cannot cross the bound.
                existing_rows = conn.execute(
                    "SELECT COUNT(*) FROM synthetic_prepared_triggers"
                ).fetchone()[0]
                assert_policy_epoch("before fixture capacity fence")
                if type(existing_rows) is not int or existing_rows >= _MAX_PREPARATIONS:
                    raise SyntheticTriggerRejected("synthetic trigger ledger capacity reached")
                try:
                    conn.execute(
                        """INSERT INTO synthetic_prepared_triggers
                           VALUES(?,?,?,?,?,?,?)""",
                        (
                            trigger, scope, policy_hash, source_digest,
                            observation_digest, observed_at_ms, now_ms,
                        ),
                    )
                except sqlite3.IntegrityError as exc:
                    raise SyntheticTriggerRejected(
                        "duplicate synthetic trigger occurrence"
                    ) from exc
                assert_policy_epoch("during preparation")
                if retained_epoch is not None and (
                    retained.row_hashes is not retained_rows_carrier
                    or (retained.row_hashes, retained.digest) != retained_epoch
                ):
                    raise SyntheticTriggerRejected("retained proactive witness changed")
                if self.path is not ledger_path:
                    raise SyntheticTriggerRejected("proactive ledger path changed before commit")
                _refuse_aliased_proactive_path(ledger_path)
                _require_original_receipt_authority()
                conn.commit()
                # A successful COMMIT is durable even when a subsequent
                # callback discovers stale input. Never erase or replay it.
                assert_policy_epoch("after trigger commit")
                if retained_epoch is not None and (
                    retained.row_hashes is not retained_rows_carrier
                    or (retained.row_hashes, retained.digest) != retained_epoch
                ):
                    raise SyntheticTriggerRejected(
                        "retained proactive witness changed after trigger commit"
                    )
                _require_original_receipt_authority()
                receipt = SyntheticTriggerReceipt(trigger, now_ms)
                # The constructor is itself a caller-observable callback. A
                # reentrant replacement may patch a slot/getter before our
                # first result lookup; reject it without executing that getter.
                _require_original_receipt_authority()
                assert_policy_epoch("after trigger receipt")
                if (
                    type(receipt) is not _RECEIPT_TYPE
                    or receipt.trigger_id is not trigger
                    or receipt.prepared_at_ms is not now_ms
                ):
                    raise SyntheticTriggerRejected("trigger receipt changed")
                # A post-COMMIT getter can be reentrant. Recheck the exact
                # receipt, policy and original denial definitions after EACH
                # query. If this fails, the preparation marker may already
                # be durable; callers must inspect it, not blindly retry.
                for name in _RECEIPT_DENIALS:
                    if getattr(receipt, name) is not False:
                        raise SyntheticTriggerRejected("trigger receipt gained authority")
                    _require_original_receipt_authority()
                    assert_policy_epoch("after trigger receipt authority")
                    if (
                        type(receipt) is not _RECEIPT_TYPE
                        or receipt.trigger_id is not trigger
                        or receipt.prepared_at_ms is not now_ms
                    ):
                        raise SyntheticTriggerRejected("trigger receipt changed")
                _require_original_receipt_authority()
                return receipt
            except BaseException:
                conn.rollback()
                raise

    def count(self) -> int:
        """Read-only count; a missing database is never recreated."""
        path_epoch = self.path
        if type(path_epoch) is not type(Path(".")):
            raise SyntheticTriggerRejected("proactive ledger path changed")
        _refuse_aliased_proactive_path(path_epoch)
        resolved = path_epoch.resolve()
        if self.path is not path_epoch:
            raise SyntheticTriggerRejected("proactive ledger path changed before opening")
        uri = resolved.as_uri() + "?mode=ro"
        if self.path is not path_epoch:
            raise SyntheticTriggerRejected("proactive ledger path changed before opening")
        with closing(sqlite3.connect(
            uri, uri=True, isolation_level=None,
        )) as conn:
            if self.path is not path_epoch:
                raise SyntheticTriggerRejected("proactive ledger path changed before opening")
            _refuse_aliased_proactive_path(path_epoch)
            conn.execute("BEGIN")
            try:
                _validate(conn)
                result = conn.execute(
                    "SELECT COUNT(*) FROM synthetic_prepared_triggers"
                ).fetchone()[0]
                if self.path is not path_epoch:
                    raise SyntheticTriggerRejected(
                        "proactive ledger path changed during count"
                    )
                _refuse_aliased_proactive_path(path_epoch)
                conn.commit()
                return result
            except BaseException:
                conn.rollback()
                raise
