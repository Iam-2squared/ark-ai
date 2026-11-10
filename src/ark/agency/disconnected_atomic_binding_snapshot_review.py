"""Read-only single-snapshot comparison of a synthetic registered WRITE.

This optional reviewer reads the stored occurrence, bound action and request
hash under the *same* SQLite transaction as the full row/audit-chain check.
Local equality is neither independently held evidence nor consent, permission,
external effect proof or authority to retry an unknown WRITE.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import Literal

from . import disconnected_atomic_preaction_ledger as _ledger_module
from .contracts import ToolCall
from .disconnected_atomic_input_review import review_atomic_input_carriers
from .disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    AtomicPreactionSnapshot,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
)
from .disconnected_atomic_registry_bridge import derive_registered_atomic_intent
from .registry import ToolRegistry

_SCAN = _ledger_module._scan
_OPEN = vars(DisconnectedAtomicPreactionLedger)["_open"]
_SNAPSHOT_FIELDS = ("witness", "occurrence_ids")
_SNAPSHOT_ORIGINALS = tuple(
    vars(AtomicPreactionSnapshot)[name] for name in _SNAPSHOT_FIELDS
)
_LOCAL_STATES = ("ABSENT", "LOCAL_MATCH", "LOCAL_CONFLICT")


class AtomicBindingSnapshotRejected(ValueError):
    """Local pre-action evidence is stale, corrupt or improperly substituted."""


@dataclass(frozen=True, slots=True)
class AtomicBindingSnapshotReview:
    occurrence_id: str
    local_state: Literal["ABSENT", "LOCAL_MATCH", "LOCAL_CONFLICT"]
    retained_count: int

    @property
    def local_binding_matches(self) -> bool:
        return self.local_state == "LOCAL_MATCH"

    @property
    def binding_proven(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_effect_proven(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def manual_review_required(self) -> bool:
        return True


def _original_reader() -> None:
    if (
        _ledger_module._scan is not _SCAN
        or vars(DisconnectedAtomicPreactionLedger).get("_open") is not _OPEN
        or any(
            vars(AtomicPreactionSnapshot).get(name) is not descriptor
            for name, descriptor in zip(
                _SNAPSHOT_FIELDS, _SNAPSHOT_ORIGINALS, strict=True,
            )
        )
    ):
        raise AtomicBindingSnapshotRejected(
            "local atomic snapshot reader definition changed"
        )


def review_registered_atomic_binding_snapshot(
    ledger: DisconnectedAtomicPreactionLedger,
    retained: AtomicPreactionWitness,
    registry: ToolRegistry,
    call: ToolCall,
    *,
    occurrence_id: str,
) -> AtomicBindingSnapshotReview:
    """Compare *local* stored binding with a current immutable registry call.

    This inspection never inserts, reserves or invokes a backend. A conflicting
    occurrence remains quarantined rather than being rebound. The retained
    witness is caller-held, so even LOCAL_MATCH is not authenticated evidence.
    """
    _original_reader()
    if (
        type(ledger) is not DisconnectedAtomicPreactionLedger
        or type(retained) is not AtomicPreactionWitness
        or type(registry) is not ToolRegistry
        or type(call) is not ToolCall
    ):
        raise AtomicBindingSnapshotRejected("exact local binding inputs required")
    try:
        claim = derive_registered_atomic_intent(
            registry, call, occurrence_id=occurrence_id,
        )
        fields = review_atomic_input_carriers(claim, retained)
        _original_reader()
        # BEGIN precedes both the full chain scan and the row lookup. SQLite
        # guarantees one coherent read snapshot, including concurrent WAL writes.
        with closing(_OPEN(ledger, read_only=True)) as conn:
            conn.execute("BEGIN")
            _original_reader()
            snapshot = _SCAN(conn)
            _original_reader()
            if (
                type(snapshot) is not AtomicPreactionSnapshot
                or type(snapshot.witness) is not AtomicPreactionWitness
                or type(snapshot.occurrence_ids) is not tuple
                or snapshot.witness != retained
                or len(snapshot.occurrence_ids) != retained.count
                or len(set(snapshot.occurrence_ids)) != retained.count
            ):
                raise AtomicBindingSnapshotRejected(
                    "local atomic retained snapshot mismatch"
                )
            rows = conn.execute(
                "SELECT bound_action_id,request_sha256 FROM intents "
                "WHERE occurrence_id=? LIMIT 2", (fields[0],),
            ).fetchall()
            _original_reader()
            if len(rows) > 1 or bool(rows) != (
                fields[0] in snapshot.occurrence_ids
            ):
                raise AtomicBindingSnapshotRejected(
                    "atomic occurrence and row snapshot disagree"
                )
        if review_atomic_input_carriers(claim, retained) != fields:
            raise AtomicBindingSnapshotRejected(
                "atomic input changed while reading local snapshot"
            )
        _original_reader()
        state = (
            "ABSENT" if not rows
            else "LOCAL_MATCH" if rows[0] == (fields[1], fields[2])
            else "LOCAL_CONFLICT"
        )
        if state not in _LOCAL_STATES:
            raise AtomicBindingSnapshotRejected("invalid local state")
        return AtomicBindingSnapshotReview(fields[0], state, fields[3])
    except (AtomicPreactionRejected, sqlite3.DatabaseError, OSError) as exc:
        raise AtomicBindingSnapshotRejected(
            "local atomic recovery binding cannot be trusted"
        ) from exc
