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
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .contracts import Effect, OneShotAuthorization, ToolCall
from .registry import ToolRegistry

_MAX = 2**63 - 1
_OCCURRENCE = re.compile(r"occ_[0-9a-f]{64}\Z")
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


def _objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        tuple(row)
        for row in conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        ).fetchall()
    )


def _validate(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise SyntheticReplayRejected("synthetic reservation schema version changed")
    with sqlite3.connect(":memory:") as expected:
        expected.execute(_TABLE)
        if _objects(conn) != _objects(expected):
            raise SyntheticReplayRejected("synthetic reservation schema changed")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise SyntheticReplayRejected("synthetic reservation storage failed quick_check")


class SyntheticOccurrenceStore:
    """No-execution fixture ledger; not a real PermissionGate or token issuer."""

    def __init__(self, path: Path) -> None:
        if type(path) is not Path:
            raise TypeError("synthetic ledger path must be an exact pathlib.Path")
        self._path = path
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if _objects(conn):
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

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, timeout=10, isolation_level=None)

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
        try:
            first = registry.bind(call)
            token_epoch = (token.token_id, token.request_id, token.expires_at_ms)
            if first.registration.effect is not Effect.WRITE:
                raise SyntheticReplayRejected("only synthetic WRITE occurrences can reserve")
            if token.request_id != first.call.request_id or token.expires_at_ms <= now_ms:
                raise SyntheticReplayRejected("synthetic token is expired or mismatched")
            token_digest = hashlib.sha256(
                ("ARK-synthetic-v1\0" + token.token_id).encode("utf-8")
            ).hexdigest()
        except (TypeError, ValueError, AttributeError, KeyError) as exc:
            raise SyntheticReplayRejected("synthetic registry binding failed") from exc

        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                _validate(conn)
                again = registry.bind(call)
                if (
                    again.bound_action_id != first.bound_action_id
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
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        return SyntheticReservationReceipt(
            occurrence_id, first.registry_revision, first.bound_action_id,
            first.call.request_id, now_ms,
        )

    def count_synthetic(self) -> int:
        """Read-only count; missing DB is never created as a side effect."""
        uri = self._path.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
            conn.execute("BEGIN")
            try:
                _validate(conn)
                count = conn.execute(
                    "SELECT COUNT(*) FROM synthetic_occurrence_reservations"
                ).fetchone()[0]
                conn.commit()
                return count
            except BaseException:
                conn.rollback()
                raise
