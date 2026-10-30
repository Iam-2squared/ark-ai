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
    bind_disconnected_fixture_result,
)
from .disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalWitness,
    ReadReceipt,
)
from .disconnected_toolbox import DisconnectedToolRequest, DisconnectedToolResult

_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_RECEIPT_TYPE = ReadReceipt
_BINDING_TYPE = DisconnectedFixtureBinding


class DisconnectedReadBridgeRejected(ValueError):
    """Cannot connect an exact local fixture and READ journal identity."""


def prepare_disconnected_read_receipt(
    step_id: str,
    request: DisconnectedToolRequest,
    result: DisconnectedToolResult,
    binding: DisconnectedFixtureBinding,
) -> ReadReceipt:
    """Recompute one fixture before forming an inert v1 READ journal row."""
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
    stable()
    stable_verified()
    if (
        type(receipt) is not _RECEIPT_TYPE
        or receipt.request_id is not request_fields[0]
        or receipt.step_id is not step_id
        or receipt.operation is not request_fields[1]
        or receipt.input_digest is not result_fields[2]
        or receipt.result_digest is not result_fields[4]
    ):
        raise DisconnectedReadBridgeRejected("READ receipt construction changed")
    stable_verified()
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
    if type(journal) is not DisconnectedReadJournal:
        raise DisconnectedReadBridgeRejected("exact detached READ journal required")
    receipt = prepare_disconnected_read_receipt(step_id, request, result, binding)
    return journal.append(receipt, retained)
