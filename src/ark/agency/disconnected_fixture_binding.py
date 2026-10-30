"""Request-bound custody for deterministic, disconnected fixture READ results.

The existing toolbox's result digest binds operation and result bytes but is
not scoped to its request ID. This opt-in binding adds a separate, namespaced
request witness without modifying toolbox v1 hashes or frozen contracts.
It recomputes the *memory-only* fixture locally; it never calls ToolBackend,
reads user files, gives consent, or authorizes an external side effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .disconnected_toolbox import (
    DisconnectedToolRejected,
    DisconnectedToolRequest,
    DisconnectedToolResult,
    execute_disconnected_fixture_tool,
)

_DOMAIN = b"ARK-disconnected-fixture-request-binding-v1\0"


class DisconnectedFixtureBindingRejected(ValueError):
    """A synthetic result cannot be attributed to the exact request epoch."""


@dataclass(frozen=True, slots=True)
class DisconnectedFixtureBinding:
    request_id: str
    operation: str
    input_digest: str
    result_digest: str
    request_bound_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_BINDING_TYPE = DisconnectedFixtureBinding


def bind_disconnected_fixture_result(
    request: DisconnectedToolRequest,
    result: DisconnectedToolResult,
) -> DisconnectedFixtureBinding:
    """Recompute one bounded fixture, then bind its hashes to request ID.

    A matching digest is only a local consistency check. It is never a
    signature, durable journal, authenticated user grant or action receipt.
    """
    if type(request) is not DisconnectedToolRequest or type(result) is not DisconnectedToolResult:
        raise DisconnectedFixtureBindingRejected("exact fixture request/result required")

    request_epoch = (
        request.request_id, request.operation, request.canonical_args_json,
    )
    result_epoch = (
        result.request_id, result.operation, result.input_digest,
        result.canonical_result_json, result.result_digest,
    )

    def unchanged() -> None:
        try:
            if (
                any(
                    current is not pinned for current, pinned in zip(
                        (request.request_id, request.operation, request.canonical_args_json),
                        request_epoch, strict=True,
                    )
                )
                or any(
                    current is not pinned for current, pinned in zip(
                        (result.request_id, result.operation, result.input_digest,
                         result.canonical_result_json, result.result_digest),
                        result_epoch, strict=True,
                    )
                )
                or type(request) is not DisconnectedToolRequest
                or type(result) is not DisconnectedToolResult
            ):
                raise DisconnectedFixtureBindingRejected("fixture carrier epoch changed")
        except (AttributeError, TypeError, ValueError) as exc:
            if type(exc) is DisconnectedFixtureBindingRejected:
                raise
            raise DisconnectedFixtureBindingRejected("invalid fixture carrier epoch") from exc

    unchanged()
    if (
        result.request_id != request.request_id
        or result.operation != request.operation
        or result.dispatch_authorized is not False
        or result.automatic_replay_authorized is not False
        or result.external_outcome_known is not False
    ):
        raise DisconnectedFixtureBindingRejected("fixture identity or authority mismatch")

    try:
        verified = execute_disconnected_fixture_tool(request)
    except DisconnectedToolRejected as exc:
        raise DisconnectedFixtureBindingRejected("fixture recomputation rejected") from exc
    unchanged()
    if (
        type(verified) is not DisconnectedToolResult
        or verified.request_id != result.request_id
        or verified.operation != result.operation
        or verified.input_digest != result.input_digest
        or verified.canonical_result_json != result.canonical_result_json
        or verified.result_digest != result.result_digest
        or verified.dispatch_authorized is not False
        or verified.automatic_replay_authorized is not False
        or verified.external_outcome_known is not False
    ):
        raise DisconnectedFixtureBindingRejected("fixture recomputation mismatch")

    # The v1 input and result hashes are unchanged. The new witness adds
    # request ID and operation domain separation to prevent cross-request
    # replay of otherwise identical synthetic READ outputs.
    data = json.dumps(
        (request_epoch[0], request_epoch[1], result_epoch[2], result_epoch[4]),
        ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    unchanged()
    fingerprint = hashlib.sha256(_DOMAIN + data).hexdigest()
    unchanged()
    bound = DisconnectedFixtureBinding(
        request_epoch[0], request_epoch[1], result_epoch[2],
        result_epoch[4], fingerprint,
    )
    unchanged()
    if (
        type(bound) is not _BINDING_TYPE
        or bound.request_id is not request_epoch[0]
        or bound.operation is not request_epoch[1]
        or bound.input_digest is not result_epoch[2]
        or bound.result_digest is not result_epoch[4]
        or bound.request_bound_digest is not fingerprint
        or bound.dispatch_authorized is not False
        or bound.external_outcome_verified is not False
        or bound.automatic_replay_authorized is not False
    ):
        raise DisconnectedFixtureBindingRejected("constructed binding changed")
    return bound
