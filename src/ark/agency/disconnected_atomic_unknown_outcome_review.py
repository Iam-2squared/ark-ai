"""Read-only COMMIT-UNKNOWN triage for inert, audit-paired atomic intents.

The retained pre-call witness is a local, caller-controlled prefix anchor.
A positive SQLite membership is not consent, a trusted clock, a dispatch
grant, an independently authenticated claim or an external side effect.
Even an unchanged local store is not evidence that an external tool was idle.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass

from . import disconnected_atomic_preaction_ledger as ledger_module

AtomicIntentClaim = ledger_module.AtomicIntentClaim
AtomicPreactionWitness = ledger_module.AtomicPreactionWitness
DisconnectedAtomicPreactionLedger = ledger_module.DisconnectedAtomicPreactionLedger

_ORIGINAL_SCAN = ledger_module._scan
_ORIGINAL_CLAIM = ledger_module._check_claim
_ORIGINAL_WITNESS = ledger_module._witness_image
_ORIGINAL_CARRIERS = ledger_module._require_original_atomic_carriers
_ORIGINAL_GENESIS = ledger_module.genesis_atomic_preaction_witness
_ORIGINAL_OPEN = vars(DisconnectedAtomicPreactionLedger)["_open"]
_RESULT_STATES = ("UNCHANGED", "LOCALLY_RECORDED", "PREEXISTING", "ADVANCED_OTHER")


class AtomicUnknownOutcomeRejected(ValueError):
    """The retained prefix or SQLite evidence cannot support safe triage."""


@dataclass(frozen=True, slots=True)
class AtomicUnknownOutcomeReview:
    occurrence_id: str
    local_state: str
    before_count: int
    observed_count: int
    locally_present: bool

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_effect_verified(self) -> bool:
        return False

    @property
    def independent_custody_verified(self) -> bool:
        return False

    @property
    def manual_review_required(self) -> bool:
        return True


_RESULT = AtomicUnknownOutcomeReview
_RESULT_FIELDS = (
    "occurrence_id", "local_state", "before_count", "observed_count",
    "locally_present", "dispatch_authorized", "automatic_replay_authorized",
    "external_effect_verified", "independent_custody_verified",
    "manual_review_required", "__init__", "__new__", "__getattribute__",
    "__getattr__",
)
_ORIGINAL_RESULT = tuple(vars(_RESULT).get(name) for name in _RESULT_FIELDS)
# SQLite is both the exception boundary and the source of local history.
# Rebound module handles or disposition sets must never redefine this reviewer.
_ORIGINAL_SQLITE = sqlite3
_ORIGINAL_LEDGER_SQLITE = ledger_module.sqlite3
_ORIGINAL_STATES = _RESULT_STATES


def _protocol() -> None:
    if (
        sqlite3 is not _ORIGINAL_SQLITE
        or ledger_module.sqlite3 is not _ORIGINAL_LEDGER_SQLITE
        or _RESULT_STATES is not _ORIGINAL_STATES
        or ledger_module._scan is not _ORIGINAL_SCAN
        or ledger_module._check_claim is not _ORIGINAL_CLAIM
        or ledger_module._witness_image is not _ORIGINAL_WITNESS
        or ledger_module._require_original_atomic_carriers is not _ORIGINAL_CARRIERS
        or ledger_module.genesis_atomic_preaction_witness is not _ORIGINAL_GENESIS
        or vars(DisconnectedAtomicPreactionLedger).get("_open") is not _ORIGINAL_OPEN
        or ledger_module.AtomicIntentClaim is not AtomicIntentClaim
        or ledger_module.AtomicPreactionWitness is not AtomicPreactionWitness
        or ledger_module.DisconnectedAtomicPreactionLedger is not DisconnectedAtomicPreactionLedger
        or AtomicUnknownOutcomeReview is not _RESULT
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_RESULT_FIELDS, _ORIGINAL_RESULT, strict=True)
        )
    ):
        raise AtomicUnknownOutcomeRejected("unknown outcome review protocol changed")
    _ORIGINAL_CARRIERS(snapshot=True)


def review_atomic_unknown_outcome(
    ledger: DisconnectedAtomicPreactionLedger,
    before: AtomicPreactionWitness,
    claim: AtomicIntentClaim,
) -> AtomicUnknownOutcomeReview:
    """Review one coherent SQLite epoch, never authorize a retry or action.

    Returns a *local* classification only. The full audit chain is validated
    in the same read transaction as both the prefix and claim-row observations.
    Any advanced history lacking this claim stays in manual quarantine.
    """
    _protocol()
    if (
        type(ledger) is not DisconnectedAtomicPreactionLedger
        or type(before) is not AtomicPreactionWitness
        or type(claim) is not AtomicIntentClaim
    ):
        raise AtomicUnknownOutcomeRejected("exact pre-action triage inputs required")
    try:
        _ORIGINAL_CLAIM(claim)
        original_before = _ORIGINAL_WITNESS(before)
        original_claim = (
            claim.occurrence_id, claim.bound_action_id, claim.request_sha256,
        )
        if (
            original_before[0] == 0
            and original_before != _ORIGINAL_WITNESS(_ORIGINAL_GENESIS())
        ):
            raise AtomicUnknownOutcomeRejected("retained genesis mismatch")

        def stable() -> None:
            _protocol()
            if (
                _ORIGINAL_WITNESS(before) != original_before
                or (claim.occurrence_id, claim.bound_action_id, claim.request_sha256)
                != original_claim
            ):
                raise AtomicUnknownOutcomeRejected("retained triage inputs changed")

        stable()
        with closing(ledger._open(read_only=True)) as connection:
            connection.execute("BEGIN")
            stable()
            snapshot = _ORIGINAL_SCAN(connection)
            stable()
            count, tip = _ORIGINAL_WITNESS(snapshot.witness)
            old_count, old_tip = original_before
            if old_count > count:
                raise AtomicUnknownOutcomeRejected("retained prefix ahead of SQLite")
            if old_count:
                prefix = connection.execute(
                    "SELECT chain_sha256 FROM intents WHERE seq = ?", (old_count,),
                ).fetchone()
                if prefix != (old_tip,):
                    raise AtomicUnknownOutcomeRejected("retained prefix altered")
            rows = connection.execute(
                "SELECT seq,bound_action_id,request_sha256 FROM intents "
                "WHERE occurrence_id = ?", (original_claim[0],),
            ).fetchall()
            stable()
            if len(rows) > 1 or bool(rows) != (original_claim[0] in snapshot.occurrence_ids):
                raise AtomicUnknownOutcomeRejected("occurrence membership ambiguous")
            if rows and rows[0][1:] != original_claim[1:]:
                raise AtomicUnknownOutcomeRejected("occurrence identity collision")
            if rows:
                state = "PREEXISTING" if rows[0][0] <= old_count else "LOCALLY_RECORDED"
            elif count == old_count:
                state = "UNCHANGED"
            else:
                state = "ADVANCED_OTHER"
            if state not in _RESULT_STATES or (count == old_count and tip != old_tip):
                raise AtomicUnknownOutcomeRejected("impossible pre-action epoch")
            stable()
        result = _RESULT(original_claim[0], state, old_count, count, bool(rows))
        _protocol()
        if (
            type(result) is not _RESULT
            or result.local_state not in _RESULT_STATES
            or result.occurrence_id != original_claim[0]
            or result.before_count != old_count
            or result.observed_count != count
            or result.locally_present is not bool(rows)
            or result.dispatch_authorized is not False
            or result.automatic_replay_authorized is not False
            or result.external_effect_verified is not False
            or result.independent_custody_verified is not False
            or result.manual_review_required is not True
        ):
            raise AtomicUnknownOutcomeRejected("triage result acquired authority")
        stable()
        return result
    except (ledger_module.AtomicPreactionRejected, sqlite3.Error) as exc:
        raise AtomicUnknownOutcomeRejected(
            "pre-action evidence invalid; manual quarantine required"
        ) from exc
