"""Bind an inert atomic intent fixture to an immutable local ToolRegistry.

This helper never reserves, approves, dispatches or invokes a backend.
Its digest cannot authenticate a human or turn a synthetic local audit into
an exactly-once real action. WRITE remains blocked pending reviewed consent.
"""

from __future__ import annotations

import hashlib
import re

from .contracts import Effect, ToolCall
from .disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
)
from .registry import BoundAction, ToolRegistration, ToolRegistry

_OCC = re.compile(r"occ_[0-9a-f]{64}\Z")
_BOUND = re.compile(r"bound_[0-9a-f]{64}\Z")
_ORIGINAL_BIND = vars(ToolRegistry)["bind"]
_ORIGINAL_REVISION = vars(ToolRegistry)["revision"]


def derive_registered_atomic_intent(
    registry: ToolRegistry,
    call: ToolCall,
    *,
    occurrence_id: str,
) -> AtomicIntentClaim:
    """Produce a digest-only inert claim for a registry-defined WRITE.

    This function does not grant permission and does not call execute().
    Occurrence identity must be supplied by a separately reviewed source.
    """
    if (
        type(registry) is not ToolRegistry
        or type(call) is not ToolCall
        or type(occurrence_id) is not str
        or _OCC.fullmatch(occurrence_id) is None
        or vars(ToolRegistry).get("bind") is not _ORIGINAL_BIND
        or vars(ToolRegistry).get("revision") is not _ORIGINAL_REVISION
    ):
        raise AtomicPreactionRejected("invalid registry-bound intent source")
    try:
        bound = registry.bind(call)
        if (
            type(bound) is not BoundAction
            or type(bound.registration) is not ToolRegistration
            or bound.call is not call
            or bound.registration.effect is not Effect.WRITE
            or type(bound.bound_action_id) is not str
            or _BOUND.fullmatch(bound.bound_action_id) is None
            or bound.registry_revision != registry.revision
            or bound.registration.name != call.tool
            or bound.registration.capability != call.capability
        ):
            raise AtomicPreactionRejected("registered action is not an exact WRITE")
        # ToolCall.request_id is a canonical act_ digest, not user consent.
        request_id = call.request_id
        if (
            type(request_id) is not str or len(request_id) != 68
            or not request_id.startswith("act_")
            or re.fullmatch(r"act_[0-9a-f]{64}\Z", request_id) is None
        ):
            raise AtomicPreactionRejected("registered request identity changed")
        request_digest = hashlib.sha256(request_id.encode("ascii")).hexdigest()
        claim = AtomicIntentClaim(
            occurrence_id, bound.bound_action_id, request_digest,
        )
        if (
            claim.occurrence_id is not occurrence_id
            or claim.bound_action_id is not bound.bound_action_id
            or claim.request_sha256 != request_digest
            or registry.revision != bound.registry_revision
        ):
            raise AtomicPreactionRejected("registered intent changed during binding")
    except (TypeError, ValueError) as exc:
        raise AtomicPreactionRejected("registered intent binding refused") from exc
    return claim
