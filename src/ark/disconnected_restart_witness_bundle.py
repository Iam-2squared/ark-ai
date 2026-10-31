"""Read-only restart comparison across three disconnected local metadata stores.

A successful match is only a local consistency observation. There is no
cross-SQLite transaction, independently authenticated writer/witness, trusted
clock, user consent, automatic replay, dispatch, or startup authorization.
The caller must retain every witness outside the corresponding SQLite file.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationWitness,
)
from .memory.disconnected_witness_ledger import (
    DisconnectedMemoryWitnessLedger,
    MemoryLedgerWitness,
)
from .personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayWitness,
)

_DOMAIN = b"ARK-disconnected-restart-witness-bundle-v1\0"
_MEMORY_LEDGER = DisconnectedMemoryWitnessLedger
_CONTEXT_LEDGER = DisconnectedContextReplayLedger
_DUE_LEDGER = DisconnectedDueReservations
_MEMORY_WITNESS = MemoryLedgerWitness
_CONTEXT_WITNESS = OfflineContextReplayWitness
_DUE_WITNESS = DueReservationWitness


class OfflineRestartWitnessRejected(ValueError):
    """One or more local startup witness observations are not stable."""


@dataclass(frozen=True, slots=True)
class OfflineRestartWitnessReport:
    memory_epochs: int
    context_requests: int
    due_occurrences: int
    fingerprint: str

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def startup_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def personal_context_use_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False


_REPORT = OfflineRestartWitnessReport


def _checked(value: object, witness_type: type, count_name: str, hash_name: str,
             authority_name: str, maximum: int) -> tuple[int, str]:
    if type(value) is not witness_type:
        raise OfflineRestartWitnessRejected("exact retained witness type required")
    try:
        count = getattr(value, count_name)
        digest = getattr(value, hash_name)
        if (
            type(count) is not int or not 0 <= count <= maximum
            or type(digest) is not str or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            or getattr(value, authority_name) is not False
        ):
            raise OfflineRestartWitnessRejected("untrusted startup witness")
    except (AttributeError, TypeError, ValueError) as exc:
        if type(exc) is OfflineRestartWitnessRejected:
            raise
        raise OfflineRestartWitnessRejected("invalid startup witness") from exc
    return count, digest


def review_disconnected_restart_witnesses(
    memory: DisconnectedMemoryWitnessLedger,
    retained_memory: MemoryLedgerWitness,
    context: DisconnectedContextReplayLedger,
    retained_context: OfflineContextReplayWitness,
    due: DisconnectedDueReservations,
    retained_due: DueReservationWitness,
) -> OfflineRestartWitnessReport:
    """Recheck all three exact local tips; never authorize execution.

    The two sweeps reduce stale observations but cannot supply an atomic
    cross-store snapshot or guarantee that stores will not change afterward.
    Increased histories require separate reconciliation, not automatic replay.
    """
    if (
        type(memory) is not _MEMORY_LEDGER
        or type(context) is not _CONTEXT_LEDGER
        or type(due) is not _DUE_LEDGER
    ):
        raise OfflineRestartWitnessRejected("exact disconnected stores required")

    carriers = (retained_memory, retained_context, retained_due)
    definitions = (
        (_MEMORY_WITNESS, "epochs", "chain_sha256", "custody_authenticated", 256),
        (_CONTEXT_WITNESS, "count", "chain_sha256", "independent_custody_proven", 512),
        (_DUE_WITNESS, "count", "fingerprint", "independent_custody_proven", 512),
    )
    original_paths = (memory._path, context._path, due._path)
    originals = tuple(
        _checked(value, *definition)
        for value, definition in zip(carriers, definitions, strict=True)
    )

    def stable() -> None:
        if (memory._path, context._path, due._path) != original_paths or any(
            source._path is not original
            for source, original in zip(
                (memory, context, due), original_paths, strict=True,
            )
        ):
            raise OfflineRestartWitnessRejected("restart store identity changed")
        for carrier, definition, saved in zip(
            carriers, definitions, originals, strict=True,
        ):
            current = _checked(carrier, *definition)
            if (
                current != saved
                or getattr(carrier, definition[1]) is not saved[0]
                or getattr(carrier, definition[2]) is not saved[1]
            ):
                raise OfflineRestartWitnessRejected("retained restart witness changed")

    def one(store: object, witness: object, expected: tuple[int, str],
            definition: tuple[object, ...]) -> None:
        stable()
        if store is memory:
            observed = memory.inspect(retained=retained_memory)
        else:
            observed = store.witness()
        stable()
        if _checked(observed, *definition) != expected:
            raise OfflineRestartWitnessRejected("local restart tip differs")
        # No callback may mutate the observed witness between its comparison
        # and the next read; references are not authenticated proof of history.
        stable()
        if _checked(observed, *definition) != expected:
            raise OfflineRestartWitnessRejected("observed restart witness changed")

    for index in (0, 1, 2, 2, 1, 0):
        store = (memory, context, due)[index]
        one(store, carriers[index], originals[index], definitions[index])
    stable()
    encoded = json.dumps(
        ("local-unverified", originals), separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    report = OfflineRestartWitnessReport(
        originals[0][0], originals[1][0], originals[2][0], digest,
    )
    stable()
    if (
        type(report) is not _REPORT
        or report.memory_epochs is not originals[0][0]
        or report.context_requests is not originals[1][0]
        or report.due_occurrences is not originals[2][0]
        or report.fingerprint is not digest
        or report.cross_store_atomicity_proven is not False
        or report.independent_custody_proven is not False
        or report.startup_authorized is not False
        or report.dispatch_authorized is not False
        or report.automatic_replay_authorized is not False
        or report.personal_context_use_authorized is not False
        or report.trusted_clock_verified is not False
    ):
        raise OfflineRestartWitnessRejected("restart report authority changed")
    return report
