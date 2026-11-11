"""Coherent read-only review of multiple registered synthetic WRITE occurrences.

All requested bindings are checked against one audited SQLite snapshot, rather
than stitching together separate per-occurrence observations. A local match is
not an approval, authenticated witness, proof of effect, or retry permission.
This optional fixture never reserves an occurrence or invokes a backend.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import Literal

from . import disconnected_atomic_preaction_ledger as _ledger_module
from .contracts import ToolCall
from .disconnected_atomic_binding_snapshot_review import (
    AtomicBindingSnapshotRejected,
    _original_reader,
)
from .disconnected_atomic_input_review import review_atomic_input_carriers
from .disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    AtomicPreactionSnapshot,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
)
from .disconnected_atomic_registry_bridge import derive_registered_atomic_intent
from .registry import ToolRegistry

_LOCAL_STATES = ("ABSENT", "LOCAL_MATCH", "LOCAL_CONFLICT")
_OCCURRENCE = re.compile(r"occ_[0-9a-f]{64}\Z")
_MAX_BATCH = 32
# Immutable ingress limits/grammar at import: never let a caller substitute a
# larger allocation budget or an accepting-all occurrence parser at runtime.
_ORIGINAL_LOCAL_STATES = _LOCAL_STATES
_ORIGINAL_OCCURRENCE = _OCCURRENCE
_ORIGINAL_MAX_BATCH = _MAX_BATCH
_SCAN = _ledger_module._scan
_OPEN = vars(DisconnectedAtomicPreactionLedger)["_open"]
_ORIGINAL_READER = _original_reader
_DERIVE = derive_registered_atomic_intent
_INPUT_REVIEW = review_atomic_input_carriers


@dataclass(frozen=True, slots=True)
class AtomicBatchBindingSnapshotReview:
    local_states: tuple[
        tuple[str, Literal["ABSENT", "LOCAL_MATCH", "LOCAL_CONFLICT"]], ...
    ]
    retained_count: int

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
    def independently_authenticated(self) -> bool:
        return False

    @property
    def manual_review_required(self) -> bool:
        return True


_RESULT = AtomicBatchBindingSnapshotReview
_RESULT_MEMBERS = (
    "local_states", "retained_count", "__init__", "__new__",
    "__getattribute__", "__getattr__", "tool_dispatch_authorized",
    "automatic_replay_authorized", "external_effect_proven",
    "independently_authenticated", "manual_review_required",
)
_ORIGINAL_MEMBERS = tuple(vars(_RESULT).get(name) for name in _RESULT_MEMBERS)


def _originals() -> None:
    _ORIGINAL_READER()
    if (
        _LOCAL_STATES is not _ORIGINAL_LOCAL_STATES
        or _OCCURRENCE is not _ORIGINAL_OCCURRENCE
        or type(_MAX_BATCH) is not int
        or _MAX_BATCH is not _ORIGINAL_MAX_BATCH
        or _original_reader is not _ORIGINAL_READER
        or derive_registered_atomic_intent is not _DERIVE
        or review_atomic_input_carriers is not _INPUT_REVIEW
        or _ledger_module._scan is not _SCAN
        or vars(DisconnectedAtomicPreactionLedger).get("_open") is not _OPEN
        or AtomicBatchBindingSnapshotReview is not _RESULT
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(
                _RESULT_MEMBERS, _ORIGINAL_MEMBERS, strict=True,
            )
        )
    ):
        raise AtomicBindingSnapshotRejected(
            "atomic batch snapshot reader definition changed"
        )


def _inputs(
    registry: ToolRegistry,
    requests: tuple[tuple[str, ToolCall], ...],
    retained: AtomicPreactionWitness,
) -> tuple[tuple[str, str, str], ...]:
    _originals()
    if (
        type(registry) is not ToolRegistry
        or type(retained) is not AtomicPreactionWitness
        or type(requests) is not tuple
        or not 1 <= len(requests) <= _MAX_BATCH
    ):
        raise AtomicBindingSnapshotRejected("invalid exact atomic batch inputs")
    seen: set[str] = set()
    bindings: list[tuple[str, str, str]] = []
    for pair in requests:
        if (
            type(pair) is not tuple or len(pair) != 2
            or type(pair[0]) is not str
            or _OCCURRENCE.fullmatch(pair[0]) is None
            or type(pair[1]) is not ToolCall
            or pair[0] in seen
        ):
            raise AtomicBindingSnapshotRejected(
                "invalid or duplicate atomic batch occurrence"
            )
        seen.add(pair[0])
        claim = _DERIVE(registry, pair[1], occurrence_id=pair[0])
        occurrence, bound, request, _, _ = _INPUT_REVIEW(claim, retained)
        bindings.append((occurrence, bound, request))
        _originals()
    return tuple(bindings)


def review_registered_atomic_binding_batch_snapshot(
    ledger: DisconnectedAtomicPreactionLedger,
    retained: AtomicPreactionWitness,
    registry: ToolRegistry,
    requests: tuple[tuple[str, ToolCall], ...],
) -> AtomicBatchBindingSnapshotReview:
    """Read all requested local bindings in one SQLite WAL snapshot, no writes.

    The full intent/audit chain and exact requested rows are read inside one
    BEGIN read transaction. A concurrent COMMIT cannot produce mixed epochs.
    Every result remains manual-only even when all local bindings match.
    """
    _originals()
    if type(ledger) is not DisconnectedAtomicPreactionLedger:
        raise AtomicBindingSnapshotRejected("exact atomic ledger required")
    try:
        expected = _inputs(registry, requests, retained)
        _originals()
        with closing(_OPEN(ledger, read_only=True)) as conn:
            conn.execute("BEGIN")
            snapshot = _SCAN(conn)
            _originals()
            if (
                type(snapshot) is not AtomicPreactionSnapshot
                or type(snapshot.witness) is not AtomicPreactionWitness
                or type(snapshot.witness.count) is not int
                or type(retained.count) is not int
                or snapshot.witness.count != retained.count
                or type(snapshot.witness.tip_sha256) is not str
                or type(retained.tip_sha256) is not str
                or snapshot.witness.tip_sha256 != retained.tip_sha256
                or type(snapshot.occurrence_ids) is not tuple
                or len(snapshot.occurrence_ids) != retained.count
                or len(set(snapshot.occurrence_ids)) != retained.count
            ):
                raise AtomicBindingSnapshotRejected(
                    "atomic batch retained snapshot mismatch"
                )
            placeholders = ",".join("?" for _ in expected)
            rows = conn.execute(
                "SELECT occurrence_id,bound_action_id,request_sha256 "
                "FROM intents WHERE occurrence_id IN (" + placeholders + ")",
                tuple(item[0] for item in expected),
            ).fetchall()
            _originals()
            found = {row[0]: (row[1], row[2]) for row in rows}
            if (
                len(found) != len(rows)
                or any(key not in snapshot.occurrence_ids for key in found)
                or any(
                    (item[0] in found) != (item[0] in snapshot.occurrence_ids)
                    for item in expected
                )
            ):
                raise AtomicBindingSnapshotRejected(
                    "atomic batch row and audit snapshot disagree"
                )
        if _inputs(registry, requests, retained) != expected:
            raise AtomicBindingSnapshotRejected(
                "atomic batch request changed during snapshot"
            )
        states: list[tuple[str, Literal[
            "ABSENT", "LOCAL_MATCH", "LOCAL_CONFLICT",
        ]]] = []
        for occurrence, bound, request in expected:
            value: Literal["ABSENT", "LOCAL_MATCH", "LOCAL_CONFLICT"] = (
                "ABSENT" if occurrence not in found
                else "LOCAL_MATCH" if found[occurrence] == (bound, request)
                else "LOCAL_CONFLICT"
            )
            if value not in _LOCAL_STATES:
                raise AtomicBindingSnapshotRejected("atomic batch state invalid")
            states.append((occurrence, value))
        _originals()
        result = _RESULT(tuple(states), retained.count)
        _originals()
        if (
            result.tool_dispatch_authorized is not False
            or result.automatic_replay_authorized is not False
            or result.external_effect_proven is not False
            or result.independently_authenticated is not False
            or result.manual_review_required is not True
        ):
            raise AtomicBindingSnapshotRejected("atomic batch result gained authority")
        _originals()
        return result
    except (AtomicPreactionRejected, sqlite3.DatabaseError, OSError) as exc:
        raise AtomicBindingSnapshotRejected(
            "atomic batch snapshot cannot be trusted"
        ) from exc

