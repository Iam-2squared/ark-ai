"""Bind memory-only fixture READ results to a detached journal receipt.

This bridge performs no ToolBackend calls, consent checks, clock attestations
or outside-world actions. Only caller-provided fixture bytes are processed.
The existing journal v1 row stores input/result hashes, not the extra
request-bound digest: retain that separate binding independently if needed.
"""

from __future__ import annotations

import re

from .disconnected_fixture_binding import (
    DisconnectedFixtureBinding,
    DisconnectedFixtureBindingRejected,
    _assert_original_binding,
    bind_disconnected_fixture_result,
)
from .disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadJournalWitness,
    ReadReceipt,
    _chain,
)
from .disconnected_toolbox import (
    DisconnectedToolRejected,
    DisconnectedToolRequest,
    DisconnectedToolResult,
    _require_original_request_carrier,
    _require_original_result_denials,
)

_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_RECEIPT_TYPE = ReadReceipt
_BINDING_TYPE = DisconnectedFixtureBinding

# Immutable instances still have mutable Python classes. Verify descriptors
# BEFORE dereferencing fixture JSON or invoking any deny-only getter.
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_BINDING_FIELDS = (
    "request_id", "operation", "input_digest", "result_digest",
    "request_bound_digest",
)
_RECEIPT_FIELDS = (
    "request_id", "step_id", "operation", "input_digest", "result_digest",
)
_ORIGINAL_BINDING_SLOTS = tuple(
    vars(_BINDING_TYPE).get(name)
    for name in _BINDING_FIELDS + _CARRIER_HOOKS
)
_ORIGINAL_RECEIPT_SLOTS = tuple(
    vars(_RECEIPT_TYPE).get(name)
    for name in _RECEIPT_FIELDS + _CARRIER_HOOKS
)


class DisconnectedReadBridgeRejected(ValueError):
    """Cannot connect an exact local fixture and READ journal identity."""

def _require_original_bridge_carriers() -> None:
    try:
        _require_original_request_carrier()
        _require_original_result_denials()
        _assert_original_binding()
    except (DisconnectedToolRejected, DisconnectedFixtureBindingRejected) as exc:
        raise DisconnectedReadBridgeRejected(
            "fixture rebinding failed: untrusted synthetic authority descriptor"
        ) from exc
    if (
        DisconnectedFixtureBinding is not _BINDING_TYPE
        or ReadReceipt is not _RECEIPT_TYPE
        or any(
            vars(_BINDING_TYPE).get(name) is not original
            for name, original in zip(
                _BINDING_FIELDS + _CARRIER_HOOKS,
                _ORIGINAL_BINDING_SLOTS, strict=True,
            )
        )
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _RECEIPT_FIELDS + _CARRIER_HOOKS,
                _ORIGINAL_RECEIPT_SLOTS, strict=True,
            )
        )
    ):
        raise DisconnectedReadBridgeRejected(
            "fixture rebinding failed: untrusted synthetic authority or receipt descriptor"
        )


def prepare_disconnected_read_receipt(
    step_id: str,
    request: DisconnectedToolRequest,
    result: DisconnectedToolResult,
    binding: DisconnectedFixtureBinding,
) -> ReadReceipt:
    """Recompute one fixture before forming an inert v1 READ journal row."""
    _require_original_bridge_carriers()
    if (
        type(step_id) is not str or _STEP.fullmatch(step_id) is None
        or type(request) is not DisconnectedToolRequest
        or type(result) is not DisconnectedToolResult
        or type(binding) is not DisconnectedFixtureBinding
    ):
        raise DisconnectedReadBridgeRejected("exact bounded READ bridge inputs required")
    request_fields = (
        request.request_id, request.operation, request.canonical_args_json,
    )
    result_fields = (
        result.request_id, result.operation, result.input_digest,
        result.canonical_result_json, result.result_digest,
    )
    binding_fields = (
        binding.request_id, binding.operation, binding.input_digest,
        binding.result_digest, binding.request_bound_digest,
    )

    def stable() -> None:
        _require_original_bridge_carriers()
        if (
            type(request) is not DisconnectedToolRequest
            or type(result) is not DisconnectedToolResult
            or type(binding) is not DisconnectedFixtureBinding
            or any(a is not b for a, b in zip(
                (request.request_id, request.operation, request.canonical_args_json),
                request_fields, strict=True,
            ))
            or any(a is not b for a, b in zip(
                (result.request_id, result.operation, result.input_digest,
                 result.canonical_result_json, result.result_digest),
                result_fields, strict=True,
            ))
            or any(a is not b for a, b in zip(
                (binding.request_id, binding.operation, binding.input_digest,
                 binding.result_digest, binding.request_bound_digest),
                binding_fields, strict=True,
            ))
        ):
            raise DisconnectedReadBridgeRejected("fixture or binding changed during bridge")

    stable()
    if (
        binding.dispatch_authorized is not False
        or binding.external_outcome_verified is not False
        or binding.automatic_replay_authorized is not False
        or result.dispatch_authorized is not False
        or result.external_outcome_known is not False
        or result.automatic_replay_authorized is not False
    ):
        raise DisconnectedReadBridgeRejected("synthetic fixture claims execution authority")
    try:
        verified = bind_disconnected_fixture_result(request, result)
    except DisconnectedFixtureBindingRejected as exc:
        raise DisconnectedReadBridgeRejected("fixture rebinding failed") from exc
    stable()
    if (
        type(verified) is not _BINDING_TYPE
        or any(a != b for a, b in zip(
            (verified.request_id, verified.operation, verified.input_digest,
             verified.result_digest, verified.request_bound_digest),
            binding_fields, strict=True,
        ))
        or verified.dispatch_authorized is not False
        or verified.external_outcome_verified is not False
        or verified.automatic_replay_authorized is not False
        or result_fields[0] != request_fields[0]
        or result_fields[1] != request_fields[1]
        or binding_fields[0] != request_fields[0]
        or binding_fields[1] != request_fields[1]
    ):
        raise DisconnectedReadBridgeRejected("READ fixture request binding mismatch")
    verified_carriers = (
        verified.request_id, verified.operation, verified.input_digest,
        verified.result_digest, verified.request_bound_digest,
    )

    def stable_verified() -> None:
        _require_original_bridge_carriers()
        if (
            type(verified) is not _BINDING_TYPE
            or any(now is not old for now, old in zip((
                verified.request_id, verified.operation, verified.input_digest,
                verified.result_digest, verified.request_bound_digest,
            ), verified_carriers, strict=True))
            or verified.dispatch_authorized is not False
            or verified.external_outcome_verified is not False
            or verified.automatic_replay_authorized is not False
        ):
            raise DisconnectedReadBridgeRejected("verified READ binding carrier changed")

    stable_verified()
    receipt = ReadReceipt(
        request_fields[0], step_id, request_fields[1],
        result_fields[2], result_fields[4],
    )
    def stable_receipt() -> None:
        _require_original_bridge_carriers()
        if (
            type(receipt) is not _RECEIPT_TYPE
            or receipt.request_id is not request_fields[0]
            or receipt.step_id is not step_id
            or receipt.operation is not request_fields[1]
            or receipt.input_digest is not result_fields[2]
            or receipt.result_digest is not result_fields[4]
        ):
            raise DisconnectedReadBridgeRejected("READ receipt construction changed")

    stable()
    stable_verified()
    stable_receipt()
    # The last authority getter on the recomputed binding is a callback.
    # Recheck the actual receipt after that callback; a frozen dataclass can
    # still be reflectively changed without modifying the recomputed binding.
    stable_verified()
    stable()
    stable_receipt()
    return receipt


def append_disconnected_fixture_read(
    journal: DisconnectedReadJournal,
    retained: ReadJournalWitness,
    step_id: str,
    request: DisconnectedToolRequest,
    result: DisconnectedToolResult,
    binding: DisconnectedFixtureBinding,
) -> ReadJournalWitness:
    """Append once to a caller-opened local journal using its retained CAS.

    Never retries: a callback error AFTER SQLite COMMIT must not be mistaken
    for a rolled-back append. The returned witness is not an action grant.
    """
    _require_original_bridge_carriers()
    if type(journal) is not DisconnectedReadJournal:
        raise DisconnectedReadBridgeRejected("exact detached READ journal required")
    receipt = prepare_disconnected_read_receipt(step_id, request, result, binding)
    # The bridge's fixture inputs outlive preparation: journal.append contains
    # SQLite/hash callback boundaries which do NOT inspect these objects.
    # Keep them pinned across the append, including its post-COMMIT epoch.
    originals = (
        (request, (request.request_id, request.operation, request.canonical_args_json)),
        (result, (
            result.request_id, result.operation, result.input_digest,
            result.canonical_result_json, result.result_digest,
        )),
        (binding, (
            binding.request_id, binding.operation, binding.input_digest,
            binding.result_digest, binding.request_bound_digest,
        )),
        (receipt, (
            receipt.request_id, receipt.step_id, receipt.operation,
            receipt.input_digest, receipt.result_digest,
        )),
    )
    prior = (retained.count, retained.tip_sha256)

    def stable() -> None:
        _require_original_bridge_carriers()
        attributes = (
            ("request_id", "operation", "canonical_args_json"),
            ("request_id", "operation", "input_digest", "canonical_result_json",
             "result_digest"),
            ("request_id", "operation", "input_digest", "result_digest",
             "request_bound_digest"),
            ("request_id", "step_id", "operation", "input_digest", "result_digest"),
        )
        if (
            type(request) is not DisconnectedToolRequest
            or type(result) is not DisconnectedToolResult
            or type(binding) is not DisconnectedFixtureBinding
            or type(receipt) is not _RECEIPT_TYPE
            or type(retained) is not ReadJournalWitness
            or retained.count is not prior[0]
            or retained.tip_sha256 is not prior[1]
            or any(
                getattr(obj, name) is not value
                for (obj, fields), names in zip(originals, attributes, strict=True)
                for name, value in zip(names, fields, strict=True)
            )
            or binding.dispatch_authorized is not False
            or binding.external_outcome_verified is not False
            or binding.automatic_replay_authorized is not False
            or result.dispatch_authorized is not False
            or result.external_outcome_known is not False
            or result.automatic_replay_authorized is not False
        ):
            raise DisconnectedReadBridgeRejected(
                "READ fixture carriers changed during journal append; "
                "commit may have happened, do not retry automatically"
            )

    stable()
    # The journal's v1 deterministic chain binds the returned tip to THIS
    # exact fixture receipt, not just to a claimed count. It is local
    # consistency evidence, never proof of an external READ or writer.
    expected_tip = _chain(prior[1], prior[0] + 1, receipt)
    stable()
    saved = journal.append(receipt, retained)
    # A failure after this point may follow a durable SQLite COMMIT.
    # Never auto-retry or claim a rollback based on this diagnostic.
    stable()
    saved_epoch = (
        saved.count, saved.tip_sha256,
    ) if type(saved) is ReadJournalWitness else ()
    if (
        type(saved) is not ReadJournalWitness
        or type(saved.count) is not int
        or saved.count != prior[0] + 1
        or type(saved.tip_sha256) is not str
        or saved.tip_sha256 != expected_tip
        or saved.dispatch_authorized is not False
        or saved.effect_proven is not False
        or saved.replay_authorized is not False
        or saved.independent_custody_proven is not False
    ):
        raise DisconnectedReadBridgeRejected(
            "untrusted READ journal result; commit status must be inspected"
        )
    stable()
    try:
        # Reopen a consistent read epoch through the journal's verifier.
        # An append callback could claim success without persisting a row.
        observed = journal.verify(saved)
    except ReadJournalRejected as exc:
        raise DisconnectedReadBridgeRejected(
            "READ journal post-append verification failed; do not retry"
        ) from exc
    stable()
    if (
        type(saved) is not ReadJournalWitness
        or saved.count is not saved_epoch[0]
        or saved.tip_sha256 is not saved_epoch[1]
        or type(observed) is not ReadJournalWitness
        or type(observed.count) is not int
        or observed.count != prior[0] + 1
        or type(observed.tip_sha256) is not str
        or observed.tip_sha256 != expected_tip
        or any(getattr(observed, flag) is not False for flag in (
            "dispatch_authorized", "effect_proven",
            "replay_authorized", "independent_custody_proven",
        ))
    ):
        raise DisconnectedReadBridgeRejected(
            "untrusted READ post-append evidence; commit status must be inspected"
        )
    # A false-valued flag getter is also a callback. Recheck both carriers
    # after the final denial rather than returning a stale proof of success.
    stable()
    if (
        type(saved) is not ReadJournalWitness
        or saved.count is not saved_epoch[0]
        or saved.tip_sha256 is not saved_epoch[1]
        or type(observed) is not ReadJournalWitness
        or observed.count != prior[0] + 1
        or observed.tip_sha256 != expected_tip
    ):
        raise DisconnectedReadBridgeRejected(
            "READ post-append witness changed; commit status must be inspected"
        )
    return saved
