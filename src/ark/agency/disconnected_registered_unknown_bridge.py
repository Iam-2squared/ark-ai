"""Read-only reconciliation of a registry-bound WRITE and an uncertain SQLite intent.

This is a *two-system local diagnostic*, not an atomic cross-store transaction.
The derived registry identity, retained prefix and local audit observation are
checked without invoking a backend, approving a WRITE or retrying an action.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import disconnected_atomic_registry_bridge as binding
from . import disconnected_atomic_unknown_outcome_review as unknown
from .contracts import ToolCall
from .disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
)
from .registry import ToolRegistry

_DOMAIN = b"ARK-registered-unknown-outcome-review-v1\0"
_STATES = ("UNCHANGED", "LOCALLY_RECORDED", "PREEXISTING", "ADVANCED_OTHER")
_ORIGINAL_BIND = binding.derive_registered_atomic_intent
_ORIGINAL_UNKNOWN = unknown.review_atomic_unknown_outcome
_ORIGINAL_BIND_GUARD = binding._require_original_bridge_dependencies
_ORIGINAL_UNKNOWN_GUARD = unknown._protocol
_ORIGINAL_SHA = hashlib.sha256
_ORIGINAL_JSON = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_STATES = _STATES


class RegisteredUnknownOutcomeRejected(ValueError):
    """Registry/intent/ledger evidence is insufficient for even local triage."""


@dataclass(frozen=True, slots=True)
class RegisteredUnknownOutcomeReview:
    occurrence_id: str
    registry_revision: str
    bound_action_id: str
    local_state: str
    before_count: int
    observed_count: int
    evidence_sha256: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def human_approval_authenticated(self) -> bool:
        return False

    @property
    def external_effect_verified(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False

    @property
    def manual_review_required(self) -> bool:
        return True


_RESULT = RegisteredUnknownOutcomeReview
_FIELDS = (
    "occurrence_id", "registry_revision", "bound_action_id", "local_state",
    "before_count", "observed_count", "evidence_sha256",
    "dispatch_authorized", "automatic_replay_authorized",
    "human_approval_authenticated", "external_effect_verified",
    "cross_store_atomicity_proven", "manual_review_required",
    "__init__", "__new__", "__getattribute__", "__getattr__",
)
_ORIGINAL_FIELDS = tuple(vars(_RESULT).get(field) for field in _FIELDS)


def _protocol() -> None:
    if (
        binding.derive_registered_atomic_intent is not _ORIGINAL_BIND
        or unknown.review_atomic_unknown_outcome is not _ORIGINAL_UNKNOWN
        or binding._require_original_bridge_dependencies is not _ORIGINAL_BIND_GUARD
        or unknown._protocol is not _ORIGINAL_UNKNOWN_GUARD
        or hashlib.sha256 is not _ORIGINAL_SHA
        or json.dumps is not _ORIGINAL_JSON
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _STATES is not _ORIGINAL_STATES
        or RegisteredUnknownOutcomeReview is not _RESULT
        or any(
            vars(_RESULT).get(name) is not old
            for name, old in zip(_FIELDS, _ORIGINAL_FIELDS, strict=True)
        )
    ):
        raise RegisteredUnknownOutcomeRejected("registered unknown protocol changed")
    _ORIGINAL_BIND_GUARD()
    _ORIGINAL_UNKNOWN_GUARD()


def review_registered_unknown_outcome(
    registry: ToolRegistry,
    call: ToolCall,
    ledger: DisconnectedAtomicPreactionLedger,
    before: AtomicPreactionWitness,
    *,
    occurrence_id: str,
) -> RegisteredUnknownOutcomeReview:
    """Compare exact registry WRITE identity to one audited SQLite epoch.

    No result is a permission token; even LOCALLY_RECORDED is not proof of
    real external execution. A caller must separately investigate UNKNOWN.
    """
    _protocol()
    if (
        type(registry) is not ToolRegistry
        or type(call) is not ToolCall
        or type(ledger) is not DisconnectedAtomicPreactionLedger
        or type(before) is not AtomicPreactionWitness
        or type(occurrence_id) is not str
    ):
        raise RegisteredUnknownOutcomeRejected("inexact registry triage inputs")
    original_path = ledger._path
    original_revision = registry.revision
    call_epoch = (call.tool, call.capability, call.scope, call.arguments, call.request_id)
    before_epoch = (before.count, before.chain_sha256)

    def stable() -> None:
        _protocol()
        if (
            ledger._path is not original_path
            or registry.revision != original_revision
            or any(
                current is not saved
                for current, saved in zip(
                    (call.tool, call.capability, call.scope, call.arguments, call.request_id),
                    call_epoch, strict=True,
                )
            )
            or (before.count, before.chain_sha256) != before_epoch
        ):
            raise RegisteredUnknownOutcomeRejected("registered triage inputs changed")

    stable()
    try:
        claim = _ORIGINAL_BIND(registry, call, occurrence_id=occurrence_id)
        stable()
        if claim.occurrence_id != occurrence_id:
            raise RegisteredUnknownOutcomeRejected("registry occurrence changed")
        claim_epoch = (claim.occurrence_id, claim.bound_action_id, claim.request_sha256)
        local = _ORIGINAL_UNKNOWN(ledger, before, claim)
        stable()
        if (
            (claim.occurrence_id, claim.bound_action_id, claim.request_sha256) != claim_epoch
            or type(local) is not unknown.AtomicUnknownOutcomeReview
            or local.occurrence_id != occurrence_id
            or local.local_state not in _STATES
            or type(local.before_count) is not int
            or type(local.observed_count) is not int
            or local.before_count != before_epoch[0]
            or local.observed_count < local.before_count
            or local.dispatch_authorized is not False
            or local.automatic_replay_authorized is not False
            or local.external_effect_verified is not False
            or local.independent_custody_verified is not False
            or local.manual_review_required is not True
        ):
            raise RegisteredUnknownOutcomeRejected("local audit review inconsistent")
        payload = json.dumps(
            (occurrence_id, original_revision, claim.bound_action_id,
             claim.request_sha256, before_epoch[0], before_epoch[1],
             local.local_state, local.observed_count),
            separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
        if len(payload) > 4096:
            raise RegisteredUnknownOutcomeRejected("registered review exceeds budget")
        digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
        stable()
        result = _RESULT(
            occurrence_id, original_revision, claim.bound_action_id,
            local.local_state, local.before_count, local.observed_count, digest,
        )
        _protocol()
        if (
            type(result) is not _RESULT
            or (result.occurrence_id, result.registry_revision, result.bound_action_id,
                result.local_state, result.before_count, result.observed_count,
                result.evidence_sha256) != (
                    occurrence_id, original_revision, claim.bound_action_id,
                    local.local_state, local.before_count, local.observed_count, digest,
                )
            or any(getattr(result, field) is not False for field in (
                "dispatch_authorized", "automatic_replay_authorized",
                "human_approval_authenticated", "external_effect_verified",
                "cross_store_atomicity_proven",
            ))
            or result.manual_review_required is not True
        ):
            raise RegisteredUnknownOutcomeRejected("registered result gained authority")
        stable()
        return result
    except (AtomicPreactionRejected, unknown.AtomicUnknownOutcomeRejected) as exc:
        raise RegisteredUnknownOutcomeRejected(
            "registry-bound unknown evidence refused; manual review required"
        ) from exc
