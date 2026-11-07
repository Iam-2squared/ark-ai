"""Join an immutable registered READ to a disconnected fixture and journal row.

The registered ToolCall uses an act_ identity; the fixture and journal use
a distinct req_ identity. This is an explicit local correlation, NOT proof
that the fixture request originated with the registered action. The caller
must retain the returned link separately: journal v1 has no link column.
No backend, external READ, WRITE, trusted clock, or replay is authorized.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .contracts import CapabilityGrant, ToolCall, _jsonable
from .disconnected_fixture_binding import DisconnectedFixtureBinding
from .disconnected_read_journal import ReadReceipt
from .disconnected_read_receipt_bridge import (
    DisconnectedReadBridgeRejected,
    prepare_disconnected_read_receipt,
)
from .disconnected_registered_read_preflight import (
    DisconnectedReadPreflight,
    DisconnectedReadPreflightRejected,
    review_disconnected_registered_read,
)
from .disconnected_toolbox import (
    DisconnectedToolRequest,
    DisconnectedToolResult,
    _canonical,
)
from .policy import PermissionGate
from .registry import ToolRegistry

_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_DOMAIN = b"ARK-registered-disconnected-fixture-link-v1\0"
_MAX_GRANTS = 128


class RegisteredFixtureLinkRejected(ValueError):
    """The disconnected fixture cannot be correlated with this READ intent."""


@dataclass(frozen=True, slots=True)
class RegisteredFixtureLink:
    step_id: str
    action_request_id: str
    fixture_request_id: str
    registry_revision: str
    bound_action_id: str
    request_bound_digest: str
    result_digest: str
    link_sha256: str

    @property
    def backend_dispatched(self) -> bool:
        return False

    @property
    def external_result_proven(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def replay_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_or_consent_proven(self) -> bool:
        return False


_RESULT = RegisteredFixtureLink
_PREFLIGHT = DisconnectedReadPreflight
_RECEIPT = ReadReceipt
_DENIALS = (
    "backend_dispatched", "external_result_proven", "write_authorized",
    "replay_authorized", "trusted_clock_or_consent_proven",
)


def review_registered_disconnected_fixture(
    registry: ToolRegistry,
    gate: PermissionGate,
    call: ToolCall,
    grants: tuple[CapabilityGrant, ...],
    step_id: str,
    request: DisconnectedToolRequest,
    result: DisconnectedToolResult,
    binding: DisconnectedFixtureBinding,
    *,
    observed_at_ms: int,
) -> RegisteredFixtureLink:
    """Make a non-authorizing local correlation before any journal append.

    The companion receipt is recomputed but NOT persisted here. This leaves
    the existing SQLite CAS/unknown-outcome boundary in the separate bridge.
    """
    if (
        type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
        or type(call) is not ToolCall
        or type(grants) is not tuple
        or len(grants) > _MAX_GRANTS
        or any(type(item) is not CapabilityGrant for item in grants)
        or type(step_id) is not str
        or _STEP.fullmatch(step_id) is None
        or type(request) is not DisconnectedToolRequest
        or type(result) is not DisconnectedToolResult
        or type(binding) is not DisconnectedFixtureBinding
        or type(observed_at_ms) is not int
        or not 0 <= observed_at_ms <= (1 << 63) - 1
    ):
        raise RegisteredFixtureLinkRejected("exact bounded registered fixture inputs required")

    call_epoch = (call.tool, call.capability, call.scope, call.arguments)
    action_request = call.request_id  # computed digest: compare value, not object identity
    request_epoch = (
        request.request_id, request.operation, request.canonical_args_json,
    )
    result_epoch = (
        result.request_id, result.operation, result.input_digest,
        result.canonical_result_json, result.result_digest,
    )
    binding_epoch = (
        binding.request_id, binding.operation, binding.input_digest,
        binding.result_digest, binding.request_bound_digest,
    )
    grant_epoch = tuple(
        (grant, grant.capability, grant.scope, grant.expires_at_ms)
        for grant in grants
    )
    try:
        registry_revision = registry.revision
    except (ValueError, TypeError) as exc:
        raise RegisteredFixtureLinkRejected("unavailable registry revision") from exc

    def stable() -> None:
        try:
            if (
                any(a is not b for a, b in zip(
                    (call.tool, call.capability, call.scope, call.arguments),
                    call_epoch, strict=True,
                ))
                or call.request_id != action_request
                or any(a is not b for a, b in zip((
                    request.request_id, request.operation,
                    request.canonical_args_json,
                ), request_epoch, strict=True))
                or any(a is not b for a, b in zip((
                    result.request_id, result.operation, result.input_digest,
                    result.canonical_result_json, result.result_digest,
                ), result_epoch, strict=True))
                or any(a is not b for a, b in zip((
                    binding.request_id, binding.operation, binding.input_digest,
                    binding.result_digest, binding.request_bound_digest,
                ), binding_epoch, strict=True))
                or any(
                    type(grant) is not CapabilityGrant
                    or grant is not original
                    or grant.capability is not capability
                    or grant.scope is not scope
                    or grant.expires_at_ms is not expiry
                    for grant, (original, capability, scope, expiry) in zip(
                        grants, grant_epoch, strict=True,
                    )
                )
                or registry.revision != registry_revision
                or result.dispatch_authorized is not False
                or result.external_outcome_known is not False
                or result.automatic_replay_authorized is not False
                or binding.dispatch_authorized is not False
                or binding.external_outcome_verified is not False
                or binding.automatic_replay_authorized is not False
            ):
                raise RegisteredFixtureLinkRejected(
                    "registered fixture input or denied authority changed"
                )
        except RegisteredFixtureLinkRejected:
            raise
        except (AttributeError, TypeError, ValueError) as exc:
            raise RegisteredFixtureLinkRejected(
                "registered fixture input epoch unavailable"
            ) from exc

    stable()
    if call_epoch[0] != request_epoch[1]:
        raise RegisteredFixtureLinkRejected("registered tool and fixture operation differ")
    try:
        args_json = _canonical(_jsonable(call_epoch[3]))
    except (TypeError, ValueError, UnicodeError, OverflowError) as exc:
        raise RegisteredFixtureLinkRejected("registered JSON arguments unavailable") from exc
    stable()
    if args_json != request_epoch[2]:
        raise RegisteredFixtureLinkRejected(
            "registered arguments do not match canonical fixture input"
        )

    try:
        preflight = review_disconnected_registered_read(
            registry, gate, call, grants, now_ms=observed_at_ms,
        )
    except DisconnectedReadPreflightRejected as exc:
        raise RegisteredFixtureLinkRejected("registry READ or grant denied") from exc
    stable()
    preflight_epoch = (
        preflight.registry_revision, preflight.bound_action_id,
        preflight.request_id, preflight.tool_name, preflight.capability,
    )

    def stable_preflight() -> None:
        if (
            type(preflight) is not _PREFLIGHT
            or any(a is not b for a, b in zip((
                preflight.registry_revision, preflight.bound_action_id,
                preflight.request_id, preflight.tool_name, preflight.capability,
            ), preflight_epoch, strict=True))
            or preflight.registry_revision != registry_revision
            or preflight.request_id != action_request
            or preflight.tool_name != call_epoch[0]
            or preflight.capability != call_epoch[1]
            or preflight.backend_dispatched is not False
            or preflight.external_read_authorized is not False
            or preflight.write_authorized is not False
            or preflight.trusted_clock_verified is not False
            or preflight.durable_permission_proven is not False
        ):
            raise RegisteredFixtureLinkRejected("registered preflight gained authority")

    stable_preflight()
    try:
        receipt = prepare_disconnected_read_receipt(
            step_id, request, result, binding,
        )
    except DisconnectedReadBridgeRejected as exc:
        raise RegisteredFixtureLinkRejected("fixture journal receipt denied") from exc
    stable()
    stable_preflight()
    if (
        type(receipt) is not _RECEIPT
        or (receipt.request_id, receipt.step_id, receipt.operation,
            receipt.input_digest, receipt.result_digest)
        != (request_epoch[0], step_id, request_epoch[1],
            result_epoch[2], result_epoch[4])
        or binding_epoch[:4] != (
            request_epoch[0], request_epoch[1], result_epoch[2], result_epoch[4],
        )
    ):
        raise RegisteredFixtureLinkRejected("journal receipt and fixture differ")

    payload = (
        step_id, action_request, request_epoch[0], registry_revision,
        preflight_epoch[1], binding_epoch[4], result_epoch[4], observed_at_ms,
    )
    digest = hashlib.sha256(
        _DOMAIN + json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    stable()
    stable_preflight()
    joined = _RESULT(*payload[:7], digest)
    stable()
    stable_preflight()
    expected = (*payload[:7], digest)

    def stable_join() -> None:
        fields = (
            joined.step_id, joined.action_request_id, joined.fixture_request_id,
            joined.registry_revision, joined.bound_action_id,
            joined.request_bound_digest, joined.result_digest, joined.link_sha256,
        )
        if (
            type(joined) is not RegisteredFixtureLink
            or any(now is not old for now, old in zip(
                fields, expected, strict=True,
            ))
            or any(getattr(joined, flag) is not False for flag in _DENIALS)
            or any(now is not old for now, old in zip((
                joined.step_id, joined.action_request_id, joined.fixture_request_id,
                joined.registry_revision, joined.bound_action_id,
                joined.request_bound_digest, joined.result_digest, joined.link_sha256,
            ), expected, strict=True))
        ):
            raise RegisteredFixtureLinkRejected("local link gained authority")

    stable_join()
    stable()
    stable_preflight()
    stable_join()
    return joined
