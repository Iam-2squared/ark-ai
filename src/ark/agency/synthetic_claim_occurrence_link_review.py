"""Disconnected approval-claim/occurrence association sidecar.

This local append-only fixture binds *untrusted claims* to already reserved
synthetic occurrences. It is NOT a credential, consent signature, production
authority, cross-SQLite transaction, effect receipt or replay instruction.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass, fields
from pathlib import Path

from .contracts import Effect, ToolCall
from .durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReservationReceipt,
    _validate as _validate_reservations,
)
from .registry import ToolRegistry
from .synthetic_approval_cancellation_fence_review import (
    review_synthetic_approval_cancellation_fence,
)
from .synthetic_approval_cancellation_review import (
    SyntheticCancellationLedger,
    SyntheticCancellationWitness,
)
from .synthetic_approval_claim_review import SyntheticApprovalEnvelope

_MAX = 2**63 - 1
_LIMIT = 10000
_APPROVAL = re.compile(r"approval_[0-9a-f]{64}\Z")
_OCCURRENCE = re.compile(r"occ_[0-9a-f]{64}\Z")
_REGISTRY = re.compile(r"tools_[0-9a-f]{64}\Z")
_BOUND = re.compile(r"bound_[0-9a-f]{64}\Z")
_REQUEST = re.compile(r"act_[0-9a-f]{64}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_LINK = re.compile(r"clink_[0-9a-f]{64}\Z")

_TABLE = """CREATE TABLE synthetic_claim_occurrence_links(
    seq INTEGER PRIMARY KEY CHECK(seq>=1),
    approval_id TEXT NOT NULL UNIQUE,
    occurrence_id TEXT NOT NULL UNIQUE,
    registry_revision TEXT NOT NULL,
    bound_action_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    issuer_digest TEXT NOT NULL,
    subject_digest TEXT NOT NULL,
    purpose_digest TEXT NOT NULL,
    recipient_digest TEXT NOT NULL,
    nonce_digest TEXT NOT NULL,
    linked_at_ms INTEGER NOT NULL CHECK(linked_at_ms>=0),
    previous_hash TEXT NOT NULL,
    link_hash TEXT NOT NULL
)"""
_ROWS = """SELECT seq,approval_id,occurrence_id,registry_revision,
                 bound_action_id,request_id,issuer_digest,subject_digest,
                 purpose_digest,recipient_digest,nonce_digest,
                 linked_at_ms,previous_hash,link_hash
          FROM synthetic_claim_occurrence_links ORDER BY seq"""


class SyntheticClaimLinkRejected(RuntimeError):
    """An unauthenticated association is malformed, stale or inconsistent."""


def _hash(label: str, values: object) -> str:
    payload = json.dumps(
        values, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return "clink_" + hashlib.sha256(label.encode("utf-8") + b"\0" + payload).hexdigest()


_GENESIS = _hash("ARK-synthetic-claim-occurrence-genesis-v1", ())


def _objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        tuple(row) for row in conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        )
    )


@dataclass(frozen=True, slots=True)
class SyntheticClaimLinkWitness:
    event_count: int
    tail_hash: str
    last_linked_at_ms: int

    def assert_shape(self) -> None:
        if (
            type(self.event_count) is not int
            or not 0 <= self.event_count <= _LIMIT
            or type(self.tail_hash) is not str
            or not _LINK.fullmatch(self.tail_hash)
            or type(self.last_linked_at_ms) is not int
            or not -1 <= self.last_linked_at_ms <= _MAX
            or (self.event_count == 0) != (self.last_linked_at_ms == -1)
            or self.event_count == 0 and self.tail_hash != _GENESIS
        ):
            raise SyntheticClaimLinkRejected("invalid synthetic claim link witness")


@dataclass(frozen=True, slots=True)
class SyntheticClaimLinkReceipt:
    approval_id: str
    occurrence_id: str
    link_hash: str

    @property
    def human_consent_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def _replay(conn: sqlite3.Connection) -> tuple[SyntheticClaimLinkWitness, ...]:
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise SyntheticClaimLinkRejected("synthetic claim link schema version changed")
    with sqlite3.connect(":memory:") as expected:
        expected.execute(_TABLE)
        if _objects(conn) != _objects(expected):
            raise SyntheticClaimLinkRejected("synthetic claim link schema changed")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise SyntheticClaimLinkRejected("synthetic claim link storage invalid")
    prefixes = [SyntheticClaimLinkWitness(0, _GENESIS, -1)]
    for row in conn.execute(_ROWS):
        previous = prefixes[-1]
        if previous.event_count >= _LIMIT:
            raise SyntheticClaimLinkRejected("synthetic claim link budget exhausted")
        seq, approval, occurrence, revision, bound, request = row[:6]
        actors = row[6:11]
        at_ms, parent, digest = row[11:]
        if (
            type(seq) is not int or seq != previous.event_count + 1
            or type(approval) is not str or not _APPROVAL.fullmatch(approval)
            or type(occurrence) is not str or not _OCCURRENCE.fullmatch(occurrence)
            or type(revision) is not str or not _REGISTRY.fullmatch(revision)
            or type(bound) is not str or not _BOUND.fullmatch(bound)
            or type(request) is not str or not _REQUEST.fullmatch(request)
            or any(type(x) is not str or not _DIGEST.fullmatch(x) for x in actors)
            or type(at_ms) is not int or not 0 <= at_ms <= _MAX
            or at_ms < previous.last_linked_at_ms
            or type(parent) is not str or parent != previous.tail_hash
            or type(digest) is not str
            or digest != _hash("ARK-synthetic-claim-occurrence-event-v1", row[:-1])
        ):
            raise SyntheticClaimLinkRejected("synthetic claim link history changed")
        prefixes.append(SyntheticClaimLinkWitness(seq, digest, at_ms))
    return tuple(prefixes)


def _check_retained(
    prefixes: tuple[SyntheticClaimLinkWitness, ...],
    retained: SyntheticClaimLinkWitness | None,
) -> None:
    if retained is not None and (
        retained.event_count >= len(prefixes)
        or prefixes[retained.event_count] != retained
    ):
        raise SyntheticClaimLinkRejected("retained claim link history changed")


def _retained_shape(retained: SyntheticClaimLinkWitness | None) -> None:
    if retained is not None:
        if type(retained) is not SyntheticClaimLinkWitness:
            raise SyntheticClaimLinkRejected("retained claim link witness has wrong type")
        retained.assert_shape()


class SyntheticClaimOccurrenceLinkStore:
    """Research-only append journal; its receipts confer no real authority."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path):
            raise TypeError("synthetic claim link path must be a Path")
        self.path = path
        with closing(self._connect(create=True)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if _objects(conn):
                        raise SyntheticClaimLinkRejected(
                            "unversioned claim link database is not empty"
                        )
                    conn.execute(_TABLE)
                    conn.execute("PRAGMA user_version=1")
                _replay(conn)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _connect(
        self, *, create: bool = False, readonly: bool = False,
    ) -> sqlite3.Connection:
        if create:
            return sqlite3.connect(self.path, timeout=10, isolation_level=None)
        mode = "ro" if readonly else "rw"
        return sqlite3.connect(
            self.path.resolve().as_uri() + "?mode=" + mode,
            uri=True, isolation_level=None, timeout=10,
        )

    def read_witness(
        self, *, retained: SyntheticClaimLinkWitness | None = None,
    ) -> SyntheticClaimLinkWitness:
        _retained_shape(retained)
        with closing(self._connect(readonly=True)) as conn:
            conn.execute("BEGIN")
            try:
                prefixes = _replay(conn)
                _check_retained(prefixes, retained)
                result = prefixes[-1]
                conn.commit()
                return result
            except BaseException:
                conn.rollback()
                raise

    def link_synthetic(
        self,
        envelope: SyntheticApprovalEnvelope,
        cancellation: SyntheticCancellationLedger,
        registry: ToolRegistry,
        call: ToolCall,
        ledger: SyntheticOccurrenceStore,
        reservation: SyntheticReservationReceipt,
        *,
        now_ms: int,
        retained: SyntheticClaimLinkWitness | None = None,
        retained_cancellation: SyntheticCancellationWitness | None = None,
    ) -> SyntheticClaimLinkReceipt:
        """Record an already-reserved claim association, NEVER authorize it."""
        if (
            type(envelope) is not SyntheticApprovalEnvelope
            or type(cancellation) is not SyntheticCancellationLedger
            or type(registry) is not ToolRegistry or type(call) is not ToolCall
            or type(ledger) is not SyntheticOccurrenceStore
            or type(reservation) is not SyntheticReservationReceipt
            or type(now_ms) is not int or not 0 <= now_ms <= _MAX
        ):
            raise SyntheticClaimLinkRejected("exact synthetic claim link inputs required")
        _retained_shape(retained)
        initial = tuple(getattr(envelope, f.name) for f in fields(SyntheticApprovalEnvelope))
        reserved = tuple(getattr(reservation, f.name) for f in fields(SyntheticReservationReceipt))
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                prefixes = _replay(conn)
                _check_retained(prefixes, retained)
                previous = prefixes[-1]
                if previous.event_count >= _LIMIT or now_ms < previous.last_linked_at_ms:
                    raise SyntheticClaimLinkRejected("claim link budget or clock regression")
                def check_claim():
                    return review_synthetic_approval_cancellation_fence(
                        envelope, registry, call, cancellation,
                        issuer_digest=envelope.issuer_digest,
                        subject_digest=envelope.subject_digest,
                        purpose_digest=envelope.purpose_digest,
                        recipient_digest=envelope.recipient_digest,
                        now_ms=now_ms, retained=retained_cancellation,
                    )
                first = check_claim()
                bound = registry.bind(call)
                if (
                    bound.registration.effect is not Effect.WRITE
                    or first.approval_id != envelope.approval_id
                    or first.bound_action_id != bound.bound_action_id
                    or reserved != (
                        reservation.occurrence_id, bound.registry_revision,
                        bound.bound_action_id, bound.call.request_id,
                        reservation.reserved_at_ms,
                    )
                    or not 0 <= reservation.reserved_at_ms <= now_ms
                ):
                    raise SyntheticClaimLinkRejected("claim/reservation binding mismatch")
                with closing(sqlite3.connect(
                    ledger._path.resolve().as_uri() + "?mode=ro",
                    uri=True, isolation_level=None,
                )) as source:
                    source.execute("BEGIN")
                    try:
                        _validate_reservations(source)
                        row = source.execute(
                            """SELECT occurrence_id,registry_revision,
                                      bound_action_id,request_id,reserved_at_ms
                               FROM synthetic_occurrence_reservations
                               WHERE occurrence_id=?""",
                            (reservation.occurrence_id,),
                        ).fetchone()
                        if row != reserved:
                            raise SyntheticClaimLinkRejected(
                                "persisted reservation differs from receipt"
                            )
                        source.commit()
                    except BaseException:
                        source.rollback()
                        raise
                second = check_claim()
                if (
                    first != second
                    or tuple(getattr(envelope, f.name) for f in fields(
                        SyntheticApprovalEnvelope
                    )) != initial
                    or tuple(getattr(reservation, f.name) for f in fields(
                        SyntheticReservationReceipt
                    )) != reserved
                    or registry.bind(call).bound_action_id != bound.bound_action_id
                ):
                    raise SyntheticClaimLinkRejected(
                        "claim, cancellation or reservation changed during admission"
                    )
                seq = previous.event_count + 1
                values = (
                    seq, envelope.approval_id, reservation.occurrence_id,
                    bound.registry_revision, bound.bound_action_id, bound.call.request_id,
                    envelope.issuer_digest, envelope.subject_digest,
                    envelope.purpose_digest, envelope.recipient_digest,
                    envelope.nonce_digest, now_ms, previous.tail_hash,
                )
                digest = _hash("ARK-synthetic-claim-occurrence-event-v1", values)
                try:
                    conn.execute(
                        """INSERT INTO synthetic_claim_occurrence_links
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (*values, digest),
                    )
                except sqlite3.IntegrityError as exc:
                    raise SyntheticClaimLinkRejected(
                        "approval or occurrence already linked"
                    ) from exc
                conn.commit()
                return SyntheticClaimLinkReceipt(
                    envelope.approval_id, reservation.occurrence_id, digest,
                )
            except BaseException:
                conn.rollback()
                raise
