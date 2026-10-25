"""Disconnected occurrence-to-audit sidecar for synthetic WRITE fixtures.

The reservation, original ActionAudit v1 and this link database are separate
SQLite transactions. A matching link never proves consent, provenance, a
trusted clock, an external side effect or an exactly-once backend operation.
There is no backend access or permission issuance in this module.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .audit import SQLiteActionAudit
from .contracts import ActionAuditEvent, Effect, ToolCall
from .durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReservationReceipt,
)
from .durable_occurrence_review import (
    _validate as _validate_reservations,
)
from .registry import ToolRegistry

_MAX = 2**63 - 1
_LIMIT = 10_000
_OCC = re.compile(r"occ_[0-9a-f]{64}\Z")
_REV = re.compile(r"tools_[0-9a-f]{64}\Z")
_BOUND = re.compile(r"bound_[0-9a-f]{64}\Z")
_REQ = re.compile(r"act_[0-9a-f]{64}\Z")
_LINK = re.compile(r"slink_[0-9a-f]{64}\Z")
_DDL = """CREATE TABLE synthetic_occurrence_audit_links(
    seq INTEGER PRIMARY KEY CHECK(seq >= 1),
    occurrence_id TEXT NOT NULL UNIQUE,
    registry_revision TEXT NOT NULL,
    bound_action_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    audit_event_id INTEGER NOT NULL UNIQUE CHECK(audit_event_id >= 1),
    audit_event_digest TEXT NOT NULL,
    linked_at_ms INTEGER NOT NULL CHECK(linked_at_ms >= 0),
    previous_hash TEXT NOT NULL,
    link_hash TEXT NOT NULL
)"""
_SELECT = """SELECT seq,occurrence_id,registry_revision,bound_action_id,request_id,
                    audit_event_id,audit_event_digest,linked_at_ms,
                    previous_hash,link_hash
             FROM synthetic_occurrence_audit_links ORDER BY seq"""


class SyntheticAuditLinkRejected(RuntimeError):
    """A synthetic cross-store audit identity cannot be safely linked."""


def _hash(label: str, fields: object) -> str:
    encoded = json.dumps(
        fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return "slink_" + hashlib.sha256(label.encode("utf-8") + b"\0" + encoded).hexdigest()


_GENESIS = _hash("ARK-audit-link-genesis-v1", ())


def _objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        tuple(row) for row in conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        )
    )


@dataclass(frozen=True, slots=True)
class SyntheticAuditLinkWitness:
    event_count: int
    tail_hash: str
    last_link_at_ms: int

    def assert_shape(self) -> None:
        if (
            type(self.event_count) is not int or not 0 <= self.event_count <= _LIMIT
            or type(self.tail_hash) is not str or not _LINK.fullmatch(self.tail_hash)
            or type(self.last_link_at_ms) is not int
            or not -1 <= self.last_link_at_ms <= _MAX
            or (self.event_count == 0) != (self.last_link_at_ms == -1)
            or self.event_count == 0 and self.tail_hash != _GENESIS
        ):
            raise SyntheticAuditLinkRejected("invalid retained synthetic link witness")


@dataclass(frozen=True, slots=True)
class SyntheticAuditLinkReceipt:
    occurrence_id: str
    audit_event_id: int
    link_hash: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


def _replay(conn: sqlite3.Connection) -> tuple[SyntheticAuditLinkWitness, ...]:
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise SyntheticAuditLinkRejected("synthetic link schema version changed")
    with sqlite3.connect(":memory:") as expected:
        expected.execute(_DDL)
        if _objects(conn) != _objects(expected):
            raise SyntheticAuditLinkRejected("synthetic link schema changed")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise SyntheticAuditLinkRejected("synthetic link SQLite integrity failed")
    prefixes = [SyntheticAuditLinkWitness(0, _GENESIS, -1)]
    for row in conn.execute(_SELECT):
        if len(prefixes) > _LIMIT:
            raise SyntheticAuditLinkRejected("synthetic link review budget exceeded")
        seq, occ, revision, bound, request, event_id, event_hash, at, previous, link = row
        current = prefixes[-1]
        fields = (seq, occ, revision, bound, request, event_id, event_hash, at, previous)
        if (
            type(seq) is not int or seq != current.event_count + 1
            or type(occ) is not str or not _OCC.fullmatch(occ)
            or type(revision) is not str or not _REV.fullmatch(revision)
            or type(bound) is not str or not _BOUND.fullmatch(bound)
            or type(request) is not str or not _REQ.fullmatch(request)
            or type(event_id) is not int or not 1 <= event_id <= _MAX
            or type(event_hash) is not str or not _LINK.fullmatch(event_hash)
            or type(at) is not int or not 0 <= at <= _MAX
            or at < current.last_link_at_ms
            or type(previous) is not str or previous != current.tail_hash
            or type(link) is not str
            or link != _hash("ARK-synthetic-audit-link-v1", fields)
        ):
            raise SyntheticAuditLinkRejected("synthetic audit link history changed")
        prefixes.append(SyntheticAuditLinkWitness(seq, link, at))
    return tuple(prefixes)


def _audit_identity(event: ActionAuditEvent) -> tuple[object, ...]:
    return (
        event.event_id, event.request_id, event.tool, event.capability,
        event.scope, event.arguments_sha256, event.outcome, event.occurred_at_ms,
    )


class SyntheticOccurrenceAuditLinkStore:
    """Append-only mock audit links, never an authorization or execution lane."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path):
            raise TypeError("synthetic link path must be a pathlib.Path")
        self._path = path
        with closing(self._connect(create=True)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if _objects(conn):
                        raise SyntheticAuditLinkRejected("unversioned link database is nonempty")
                    conn.execute(_DDL)
                    conn.execute("PRAGMA user_version=1")
                _replay(conn)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _connect(self, *, create: bool = False, readonly: bool = False) -> sqlite3.Connection:
        if create:
            return sqlite3.connect(self._path, timeout=10, isolation_level=None)
        uri = self._path.resolve().as_uri() + ("?mode=ro" if readonly else "?mode=rw")
        return sqlite3.connect(uri, uri=True, timeout=10, isolation_level=None)

    def read_witness(
        self, *, retained: SyntheticAuditLinkWitness | None = None,
    ) -> SyntheticAuditLinkWitness:
        """One read-only local snapshot; caller must retain earlier evidence separately."""
        path_epoch = self._path
        if not isinstance(path_epoch, Path):
            raise SyntheticAuditLinkRejected("synthetic link source must retain a Path")
        if retained is not None and type(retained) is not SyntheticAuditLinkWitness:
            raise SyntheticAuditLinkRejected("retained link witness has wrong type")
        # Frozen dataclasses can still be changed reflectively: preserve the
        # original carriers rather than only their equality to a later value.
        retained_epoch = None if retained is None else (
            retained.event_count, retained.tail_hash, retained.last_link_at_ms,
        )

        def assert_epoch() -> None:
            if self._path is not path_epoch or (
                retained is not None
                and (
                    retained.event_count is not retained_epoch[0]
                    or retained.tail_hash is not retained_epoch[1]
                    or retained.last_link_at_ms is not retained_epoch[2]
                )
            ):
                raise SyntheticAuditLinkRejected(
                    "synthetic link source or retained witness changed during read"
                )

        assert_epoch()
        if retained is not None:
            retained.assert_shape()
            assert_epoch()
        with closing(self._connect(readonly=True)) as conn:
            assert_epoch()
            conn.execute("BEGIN")
            try:
                assert_epoch()
                prefixes = _replay(conn)
                assert_epoch()
                if retained is not None and (
                    retained.event_count >= len(prefixes)
                    or prefixes[retained.event_count] != retained
                ):
                    raise SyntheticAuditLinkRejected("retained synthetic link history changed")
                assert_epoch()
                result = prefixes[-1]
                conn.commit()
                assert_epoch()
            except BaseException:
                conn.rollback()
                raise
        assert_epoch()
        return result

    def link_synthetic(
        self,
        registry: ToolRegistry,
        call: ToolCall,
        ledger: SyntheticOccurrenceStore,
        reservation: SyntheticReservationReceipt,
        audit: SQLiteActionAudit,
        event: ActionAuditEvent,
        *,
        at_ms: int,
        retained: SyntheticAuditLinkWitness | None = None,
    ) -> SyntheticAuditLinkReceipt:
        """Link two existing synthetic records, without dispatch or cross-store atomicity."""
        if (
            type(registry) is not ToolRegistry or type(call) is not ToolCall
            or type(ledger) is not SyntheticOccurrenceStore
            or type(reservation) is not SyntheticReservationReceipt
            or type(audit) is not SQLiteActionAudit
            or type(event) is not ActionAuditEvent
            or type(at_ms) is not int or not 0 <= at_ms <= _MAX
        ):
            raise SyntheticAuditLinkRejected("exact synthetic link inputs required")
        if retained is not None and type(retained) is not SyntheticAuditLinkWitness:
            raise SyntheticAuditLinkRejected("retained link witness has wrong type")
        # Freeze original input and source *carriers* before any nested shape,
        # registry, SQLite or hash callback. Equal-valued substitutions are
        # still epoch changes. This is local custody, not a cross-store proof.
        link_path_epoch = self._path
        ledger_path_epoch = ledger._path
        audit_path_epoch = audit.path
        call_epoch = (call.tool, call.capability, call.scope, call.arguments)
        reservation_epoch = (
            reservation.occurrence_id, reservation.registry_revision,
            reservation.bound_action_id, reservation.request_id,
            reservation.reserved_at_ms,
        )
        event_epoch = _audit_identity(event)
        retained_epoch = None if retained is None else (
            retained.event_count, retained.tail_hash, retained.last_link_at_ms,
        )

        def assert_input_epoch() -> None:
            try:
                stable = (
                    self._path is link_path_epoch
                    and ledger._path is ledger_path_epoch
                    and audit.path is audit_path_epoch
                    and all(left is right for left, right in zip(
                        (call.tool, call.capability, call.scope, call.arguments),
                        call_epoch, strict=True,
                    ))
                    and all(left is right for left, right in zip(
                        (
                            reservation.occurrence_id, reservation.registry_revision,
                            reservation.bound_action_id, reservation.request_id,
                            reservation.reserved_at_ms,
                        ),
                        reservation_epoch, strict=True,
                    ))
                    and all(left is right for left, right in zip(
                        _audit_identity(event), event_epoch, strict=True,
                    ))
                    and (
                        retained is None or all(
                            left is right for left, right in zip(
                                (
                                    retained.event_count, retained.tail_hash,
                                    retained.last_link_at_ms,
                                ),
                                retained_epoch, strict=True,
                            )
                        )
                    )
                )
            except (AttributeError, TypeError, ValueError) as exc:
                raise SyntheticAuditLinkRejected(
                    "synthetic link original input or source changed during append"
                ) from exc
            if not stable:
                raise SyntheticAuditLinkRejected(
                    "synthetic link original input or source changed during append"
                )

        assert_input_epoch()
        if retained is not None:
            retained.assert_shape()
            assert_input_epoch()
        try:
            first = registry.bind(call)
            assert_input_epoch()
            if first.registration.effect is not Effect.WRITE:
                raise SyntheticAuditLinkRejected("only synthetic WRITE may be linked")
            if (
                reservation.registry_revision != first.registry_revision
                or reservation.bound_action_id != first.bound_action_id
                or reservation.request_id != first.call.request_id
                or type(reservation.occurrence_id) is not str
                or not _OCC.fullmatch(reservation.occurrence_id)
                or type(reservation.reserved_at_ms) is not int
                or not 0 <= reservation.reserved_at_ms <= at_ms
            ):
                raise SyntheticAuditLinkRejected("synthetic reservation binding mismatch")
            event_fields = _audit_identity(event)
            if (
                type(event.event_id) is not int or not 1 <= event.event_id <= _MAX
                or event.request_id != first.call.request_id
                or (event.tool, event.capability, event.scope, event.arguments_sha256)
                != (call.tool, call.capability, call.scope, call.arguments_sha256)
                or event.outcome != "synthetic_audit_before_mock"
                or type(event.occurred_at_ms) is not int
                or not reservation.reserved_at_ms <= event.occurred_at_ms <= at_ms
            ):
                raise SyntheticAuditLinkRejected("synthetic pre-action audit mismatch")
            event_hash = _hash("ARK-synthetic-preaction-audit-v1", event_fields)
            assert_input_epoch()
        except (TypeError, ValueError, AttributeError, KeyError) as exc:
            raise SyntheticAuditLinkRejected("synthetic identity malformed") from exc

        assert_input_epoch()
        with closing(self._connect()) as conn:
            assert_input_epoch()
            conn.execute("BEGIN IMMEDIATE")
            try:
                assert_input_epoch()
                prefixes = _replay(conn)
                assert_input_epoch()
                if retained is not None and (
                    retained.event_count >= len(prefixes)
                    or prefixes[retained.event_count] != retained
                ):
                    raise SyntheticAuditLinkRejected("retained link history changed before append")
                assert_input_epoch()
                previous = prefixes[-1]
                if previous.event_count >= _LIMIT or at_ms < previous.last_link_at_ms:
                    raise SyntheticAuditLinkRejected("synthetic link capacity or clock regression")
                # The source ledgers are separately snapshotted. This is not an
                # atomic three-database proof: future modification still races.
                assert_input_epoch()
                uri = ledger._path.resolve().as_uri() + "?mode=ro"
                assert_input_epoch()
                with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as source:
                    assert_input_epoch()
                    source.execute("BEGIN")
                    assert_input_epoch()
                    _validate_reservations(source)
                    assert_input_epoch()
                    row = source.execute(
                        """SELECT occurrence_id,registry_revision,bound_action_id,
                                  request_id,reserved_at_ms
                           FROM synthetic_occurrence_reservations WHERE occurrence_id=?""",
                        (reservation.occurrence_id,),
                    ).fetchone()
                    assert_input_epoch()
                    if row != (
                        reservation.occurrence_id, first.registry_revision,
                        first.bound_action_id, first.call.request_id,
                        reservation.reserved_at_ms,
                    ):
                        raise SyntheticAuditLinkRejected("stored reservation differs from receipt")
                    assert_input_epoch()
                    source.commit()
                    assert_input_epoch()
                assert_input_epoch()
                observed = audit.events(after_event_id=event.event_id - 1, limit=1)
                assert_input_epoch()
                if len(observed) != 1 or _audit_identity(observed[0]) != event_fields:
                    raise SyntheticAuditLinkRejected("stored audit differs from receipt")
                again = registry.bind(call)
                assert_input_epoch()
                if (
                    again.registry_revision != first.registry_revision
                    or again.bound_action_id != first.bound_action_id
                    or again.registration is not first.registration
                    or again.call is not first.call
                    or _audit_identity(event) != event_fields
                    or reservation.registry_revision != first.registry_revision
                    or reservation.bound_action_id != first.bound_action_id
                    or reservation.request_id != first.call.request_id
                ):
                    raise SyntheticAuditLinkRejected("synthetic link identity changed mid-review")
                seq = previous.event_count + 1
                fields = (
                    seq, reservation.occurrence_id, first.registry_revision,
                    first.bound_action_id, first.call.request_id, event.event_id,
                    event_hash, at_ms, previous.tail_hash,
                )
                link = _hash("ARK-synthetic-audit-link-v1", fields)
                assert_input_epoch()
                try:
                    conn.execute(
                        "INSERT INTO synthetic_occurrence_audit_links VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (*fields, link),
                    )
                except sqlite3.IntegrityError as exc:
                    raise SyntheticAuditLinkRejected(
                        "synthetic occurrence or audit already linked"
                    ) from exc
                assert_input_epoch()
                conn.commit()
                # A post-COMMIT rejection does not erase an already committed
                # link. Keep durable evidence and deny the diagnostic receipt.
                assert_input_epoch()
                return SyntheticAuditLinkReceipt(reservation_epoch[0], event_epoch[0], link)
            except BaseException:
                conn.rollback()
                raise
