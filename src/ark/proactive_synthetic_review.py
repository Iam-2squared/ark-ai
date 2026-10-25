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
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

_MAX = 2**63 - 1
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
        for name in ("owner", "namespace", "definition_id", "policy_revision"):
            _text(name, getattr(self, name))
        for name in ("revision", "minimum_interval_ms", "rolling_window_ms",
                     "max_preparations_per_window"):
            _int(name, getattr(self, name), minimum=1)

    def identity(self) -> tuple[object, ...]:
        self.__post_init__()
        return (
            self.owner, self.namespace, self.definition_id, self.revision,
            self.policy_revision, self.minimum_interval_ms,
            self.rolling_window_ms, self.max_preparations_per_window,
        )


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


def _objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(map(tuple, conn.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    )))


def _validate(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise SyntheticTriggerRejected("trigger fixture schema version changed")
    with sqlite3.connect(":memory:") as expected:
        expected.execute(_TABLE)
        if _objects(conn) != _objects(expected):
            raise SyntheticTriggerRejected("trigger fixture schema changed")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise SyntheticTriggerRejected("trigger fixture integrity failed")
    rows = conn.execute(
        """SELECT trigger_id,scope_digest,policy_digest,source_digest,
                  observation_digest,observed_at_ms,prepared_at_ms
           FROM synthetic_prepared_triggers"""
    )
    for index, row in enumerate(rows):
        if index >= 10_000:
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


class SyntheticProactiveLedger:
    """SQLite CAS-like admission for offline preparations, no execution."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path):
            raise TypeError("synthetic proactive path must be a Path")
        self.path = path
        with closing(sqlite3.connect(path, timeout=10, isolation_level=None)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if _objects(conn):
                        raise SyntheticTriggerRejected(
                            "unversioned trigger fixture is not empty"
                        )
                    conn.execute(_TABLE)
                    conn.execute("PRAGMA user_version=1")
                _validate(conn)
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
        if not isinstance(ledger_path, Path):
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
            if (
                self.path is not ledger_path
                or any(
                    getattr(policy, name) is not carrier
                    for name, carrier in zip(policy_names, policy_carriers)
                )
            ):
                raise SyntheticTriggerRejected(
                    f"policy or ledger path changed {stage}"
                )
            if policy.identity() != pinned or self.path is not ledger_path or any(
                getattr(policy, name) is not carrier
                for name, carrier in zip(policy_names, policy_carriers)
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
                receipt = SyntheticTriggerReceipt(trigger, now_ms)
                assert_policy_epoch("after trigger receipt")
                if (
                    type(receipt) is not SyntheticTriggerReceipt
                    or receipt.trigger_id != trigger
                    or receipt.prepared_at_ms != now_ms
                ):
                    raise SyntheticTriggerRejected("trigger receipt changed")
                return receipt
            except BaseException:
                conn.rollback()
                raise

    def count(self) -> int:
        """Read-only count; a missing database is never recreated."""
        path_epoch = self.path
        if not isinstance(path_epoch, Path):
            raise SyntheticTriggerRejected("proactive ledger path changed")
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
                conn.commit()
                return result
            except BaseException:
                conn.rollback()
                raise
