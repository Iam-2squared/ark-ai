"""Bind an inert atomic intent fixture to an immutable local ToolRegistry.

This helper never reserves, approves, dispatches or invokes a backend.
Its digest cannot authenticate a human or turn a synthetic local audit into
an exactly-once real action. WRITE remains blocked pending reviewed consent.
"""

from __future__ import annotations

import hashlib
import re

from . import disconnected_atomic_preaction_ledger as preaction_module
from .contracts import Effect, ToolCall
from .disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
)
from .registry import (
    BoundAction,
    ToolRegistration,
    ToolRegistry,
    _require_original_toolcall_contract,
)

_OCC = re.compile(r"occ_[0-9a-f]{64}\Z")
_BOUND = re.compile(r"bound_[0-9a-f]{64}\Z")
_ORIGINAL_BIND = vars(ToolRegistry)["bind"]
_ORIGINAL_REVISION = vars(ToolRegistry)["revision"]

_REQUEST = re.compile(r"act_[0-9a-f]{64}\Z")
_ORIGINAL_OCC = _OCC
_ORIGINAL_BOUND = _BOUND
_ORIGINAL_REQUEST = _REQUEST
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_RE = re
_ORIGINAL_CALL_GUARD = _require_original_toolcall_contract
_ORIGINAL_CLAIM_GUARD = preaction_module._require_original_atomic_carriers


def _require_original_bridge_dependencies() -> None:
    """Refuse changed hash/grammar authorities before binding an inert WRITE."""
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or re is not _ORIGINAL_RE
        or _OCC is not _ORIGINAL_OCC
        or _BOUND is not _ORIGINAL_BOUND
        or _REQUEST is not _ORIGINAL_REQUEST
        or _require_original_toolcall_contract is not _ORIGINAL_CALL_GUARD
        or preaction_module._require_original_atomic_carriers is not _ORIGINAL_CLAIM_GUARD
    ):
        raise AtomicPreactionRejected("registry intent digest or grammar changed")



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
    _require_original_bridge_dependencies()
    if (
        type(registry) is not ToolRegistry
        or type(call) is not ToolCall
        or type(occurrence_id) is not str
        or _OCC.fullmatch(occurrence_id) is None
        or vars(ToolRegistry).get("bind") is not _ORIGINAL_BIND
        or vars(ToolRegistry).get("revision") is not _ORIGINAL_REVISION
        or "bind" in vars(registry)
    ):
        raise AtomicPreactionRejected("invalid registry-bound intent source")
    _ORIGINAL_CALL_GUARD()
    # Class-level method checks do not reject an instance-shadowed bind.
    # Record the original call identity and recheck it after every callback.
    call_epoch = (call.tool, call.capability, call.scope, call.arguments, call.request_id)

    def assert_call_epoch() -> None:
        _require_original_bridge_dependencies()
        _ORIGINAL_CALL_GUARD()
        if (
            "bind" in vars(registry)
            or any(now is not original for now, original in zip(
                (call.tool, call.capability, call.scope, call.arguments),
                call_epoch[:4], strict=True,
            ))
            or call.request_id != call_epoch[4]
        ):
            raise AtomicPreactionRejected("registered intent input epoch changed")

    try:
        assert_call_epoch()
        bound = registry.bind(call)
        assert_call_epoch()
        _require_original_bridge_dependencies()
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
        assert_call_epoch()
        if (
            type(request_id) is not str or len(request_id) != 68
            or not request_id.startswith("act_")
            or _REQUEST.fullmatch(request_id) is None
        ):
            raise AtomicPreactionRejected("registered request identity changed")
        _require_original_bridge_dependencies()
        request_digest = hashlib.sha256(request_id.encode("ascii")).hexdigest()
        _require_original_bridge_dependencies()
        # Guard the exact claim carrier before invoking its Python constructor.
        _ORIGINAL_CLAIM_GUARD(snapshot=False)
        claim = AtomicIntentClaim(
            occurrence_id, bound.bound_action_id, request_digest,
        )
        _ORIGINAL_CLAIM_GUARD(snapshot=False)
        assert_call_epoch()
        _require_original_bridge_dependencies()
        if (
            claim.occurrence_id is not occurrence_id
            or claim.bound_action_id is not bound.bound_action_id
            or claim.request_sha256 != request_digest
            or registry.revision != bound.registry_revision
        ):
            raise AtomicPreactionRejected("registered intent changed during binding")
    except (TypeError, ValueError) as exc:
        raise AtomicPreactionRejected("registered intent binding refused") from exc
    _require_original_bridge_dependencies()
    _ORIGINAL_CLAIM_GUARD(snapshot=False)
    assert_call_epoch()
    return claim
