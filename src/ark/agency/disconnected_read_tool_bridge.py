"""Bounded memory-only integration of recovered READ DAGs with fixture tools.

This is a disconnected dry-run. There is NO ToolBackend, registry-bound
authority, authenticated prior result, clock, persistence, consent or
authorization to execute/replay any real action. RUNNING and UNKNOWN steps
are quarantined, not retried; only NOT_STARTED steps independently marked
READY_MOCK_ONLY can run deterministic in-memory fixtures.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

from . import disconnected_read_recovery_schedule as recovery
from . import disconnected_toolbox as fixture

_DOMAIN = b"ARK-disconnected-read-tool-preview-v1\0"
_REQUEST = re.compile(r"req_[0-9a-f]{32}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_MAX_STEPS = 24
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_RECOVERY = recovery.schedule_detached_read_recovery
_ORIGINAL_EXECUTE = fixture.execute_disconnected_fixture_tool
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_REQUEST = _REQUEST
_ORIGINAL_STEP = _STEP
_ORIGINAL_MAX_STEPS = _MAX_STEPS
_ORIGINAL_FIXTURE_DOMAIN = fixture._DOMAIN
_ORIGINAL_FIXTURE_RESULT = fixture.DisconnectedToolResult
_ORIGINAL_FIXTURE_REQUEST = fixture.DisconnectedToolRequest


class DisconnectedReadToolBridgeRejected(ValueError):
    """The synthetic recovery and fixture inputs cannot be linked safely."""


@dataclass(frozen=True, slots=True)
class DetachedReadToolBinding:
    step_id: str
    request: fixture.DisconnectedToolRequest = field(repr=False)


@dataclass(frozen=True, slots=True)
class DetachedReadToolPreview:
    request_id: str
    schedule_digest: str
    ready_step_ids: tuple[str, ...]
    withheld_step_ids: tuple[str, ...]
    fixture_results: tuple[fixture.DisconnectedToolResult, ...] = field(repr=False)
    fingerprint: str = ""

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
    def consent_authenticated(self) -> bool:
        return False


_BINDING_TYPE = DetachedReadToolBinding
_RESULT_TYPE = DetachedReadToolPreview
_BINDING_FIELDS = ("step_id", "request")
_RESULT_FIELDS = (
    "request_id", "schedule_digest", "ready_step_ids",
    "withheld_step_ids", "fixture_results", "fingerprint",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_BINDING = tuple(vars(_BINDING_TYPE).get(x) for x in (*_BINDING_FIELDS, *_HOOKS))
_ORIGINAL_RESULT = tuple(vars(_RESULT_TYPE).get(x) for x in (*_RESULT_FIELDS, *_HOOKS))
_DENIALS = (
    "dispatch_authorized", "automatic_replay_authorized",
    "external_effect_verified", "consent_authenticated",
)
_ORIGINAL_DENIALS = tuple(vars(_RESULT_TYPE)[name] for name in _DENIALS)


def _protocol() -> None:
    # Detect local substitution before passing private fixture JSON to tools.
    # This cannot attest independent code identity or malicious Python code.
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or recovery.schedule_detached_read_recovery is not _ORIGINAL_RECOVERY
        or fixture.execute_disconnected_fixture_tool is not _ORIGINAL_EXECUTE
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _REQUEST is not _ORIGINAL_REQUEST
        or _STEP is not _ORIGINAL_STEP
        or fixture._DOMAIN is not _ORIGINAL_FIXTURE_DOMAIN
        or fixture.DisconnectedToolResult is not _ORIGINAL_FIXTURE_RESULT
        or fixture.DisconnectedToolRequest is not _ORIGINAL_FIXTURE_REQUEST
        or type(_MAX_STEPS) is not int
        or _MAX_STEPS != _ORIGINAL_MAX_STEPS
        or DetachedReadToolBinding is not _BINDING_TYPE
        or DetachedReadToolPreview is not _RESULT_TYPE
        or any(
            vars(kind).get(name) is not expected
            for kind, fields, originals in (
                (_BINDING_TYPE, _BINDING_FIELDS, _ORIGINAL_BINDING),
                (_RESULT_TYPE, _RESULT_FIELDS, _ORIGINAL_RESULT),
            )
            for name, expected in zip((*fields, *_HOOKS), originals, strict=True)
        )
        or any(
            vars(_RESULT_TYPE).get(name) is not expected
            for name, expected in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise DisconnectedReadToolBridgeRejected("mock bridge protocol changed")


def derive_disconnected_read_fixture_id(request_id: str, step_id: str) -> str:
    """Bind one synthetic step to a unique memory-only fixture request ID."""
    _protocol()
    if (
        type(request_id) is not str or _REQUEST.fullmatch(request_id) is None
        or type(step_id) is not str or _STEP.fullmatch(step_id) is None
    ):
        raise DisconnectedReadToolBridgeRejected("invalid exact READ fixture identity")
    encoded = (request_id + "\0" + step_id).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + b"request\0" + encoded).hexdigest()
    _protocol()
    return "req_" + digest[:32]


def preview_disconnected_read_tools(
    request_id: str,
    steps: tuple[recovery.ReadRecoveryStep, ...],
    bindings: tuple[DetachedReadToolBinding, ...],
) -> DetachedReadToolPreview:
    """Dry-run ONLY currently READY synthetic READ steps, never external tools.

    The ordered bindings must correspond exactly to READY_MOCK_ONLY steps.
    Any binding for quarantined, terminal or already-complete steps is rejected
    before accessing its opaque arguments. Dependency state is caller asserted.
    """
    _protocol()
    if (
        type(request_id) is not str or _REQUEST.fullmatch(request_id) is None
        or type(steps) is not tuple or not 1 <= len(steps) <= _MAX_STEPS
        or any(type(s) is not recovery.ReadRecoveryStep for s in steps)
        or type(bindings) is not tuple or len(bindings) > len(steps)
        or any(type(b) is not _BINDING_TYPE for b in bindings)
    ):
        raise DisconnectedReadToolBridgeRejected("invalid bounded bridge inputs")

    input_steps = tuple(steps)
    input_bindings = tuple(bindings)
    step_epoch = tuple(
        (s.step_id, s.operation, s.depends_on, s.state, s.result_sha256)
        for s in steps
    )
    binding_epoch = tuple((b.step_id, b.request) for b in bindings)

    def stable() -> None:
        _protocol()
        if (
            len(steps) != len(input_steps) or len(bindings) != len(input_bindings)
            or any(
                row is not old or any(now is not was for now, was in zip(
                    (row.step_id, row.operation, row.depends_on,
                     row.state, row.result_sha256), fields, strict=True,
                ))
                for row, old, fields in zip(steps, input_steps, step_epoch, strict=True)
            )
            or any(
                b is not old or b.step_id is not fields[0]
                or b.request is not fields[1]
                for b, old, fields in zip(
                    bindings, input_bindings, binding_epoch, strict=True,
                )
            )
        ):
            raise DisconnectedReadToolBridgeRejected("bridge input changed")

    stable()
    plan = recovery.schedule_detached_read_recovery(request_id, steps)
    stable()
    if (
        type(plan) is not recovery.DetachedReadRecoverySchedule
        or plan.dispatch_authorized is not False
        or plan.automatic_replay_authorized is not False
        or plan.external_outcome_verified is not False
    ):
        raise DisconnectedReadToolBridgeRejected("recovery schedule is not inert")
    planned_decisions = tuple((d.step_id, d.disposition) for d in plan.decisions)
    ready = tuple(name for name, state in planned_decisions if state == "READY_MOCK_ONLY")
    withheld = tuple(name for name, state in planned_decisions if state != "READY_MOCK_ONLY")
    if (
        len(planned_decisions) != len(steps)
        or len(bindings) != len(ready)
        or tuple(b.step_id for b in bindings) != ready
    ):
        raise DisconnectedReadToolBridgeRejected("bindings must match READY READ steps")
    operations = {fields[0]: fields[1] for fields in step_epoch}
    results: list[fixture.DisconnectedToolResult] = []
    receipt_epochs: list[
        tuple[fixture.DisconnectedToolResult, tuple[str, ...]]
    ] = []

    def check_receipts() -> None:
        _protocol()
        for receipt, saved in receipt_epochs:
            if (
                type(receipt) is not _ORIGINAL_FIXTURE_RESULT
                or any(
                    getattr(receipt, field) is not value
                    for field, value in zip(
                        ("request_id", "operation", "input_digest",
                         "canonical_result_json", "result_digest"),
                        saved, strict=True,
                    )
                )
            ):
                raise DisconnectedReadToolBridgeRejected(
                    "mock receipt changed after execution"
                )

    manifest: list[tuple[str, str, str]] = []
    for binding in bindings:
        stable()
        request = binding.request
        if (
            type(request) is not fixture.DisconnectedToolRequest
            or request.operation != operations[binding.step_id]
            or request.request_id != derive_disconnected_read_fixture_id(
                request_id, binding.step_id,
            )
        ):
            raise DisconnectedReadToolBridgeRejected("READ fixture identity mismatch")
        # Only the fixed disconnected fixture executor is invoked, never a
        # real ToolBackend or an arbitrary registry registration.
        stable()
        result = fixture.execute_disconnected_fixture_tool(request)
        stable()
        if (
            type(result) is not fixture.DisconnectedToolResult
            or result.dispatch_authorized is not False
            or result.automatic_replay_authorized is not False
            or result.external_outcome_known is not False
            or result.request_id != request.request_id
            or result.operation != request.operation
        ):
            raise DisconnectedReadToolBridgeRejected("fixture result gained authority")
        # A disconnected fixture receipt is not provenance. Its asserted
        # hashes must at least match the actual bounded input and output
        # bytes before either value enters a higher-level manifest.
        receipt = (
            result.request_id, result.operation, result.input_digest,
            result.canonical_result_json, result.result_digest,
        )
        if (
            any(type(value) is not str for value in receipt)
            or len(receipt[2]) != 64 or len(receipt[4]) != 64
            or len(receipt[3].encode("utf-8", errors="strict")) > 16_384
        ):
            raise DisconnectedReadToolBridgeRejected("invalid mock receipt fields")
        expected_input = hashlib.sha256(
            _ORIGINAL_FIXTURE_DOMAIN
            + request.canonical_args_json.encode("utf-8", errors="strict")
        ).hexdigest()
        _protocol()
        expected_output = hashlib.sha256(
            _ORIGINAL_FIXTURE_DOMAIN + request.operation.encode("ascii")
            + b"\0" + receipt[3].encode("utf-8", errors="strict")
        ).hexdigest()
        _protocol()
        if (
            receipt[0] != request.request_id
            or receipt[1] != request.operation
            or receipt[2] != expected_input
            or receipt[4] != expected_output
        ):
            raise DisconnectedReadToolBridgeRejected(
                "mock receipt digest or identity mismatch"
            )
        check_receipts()
        results.append(result)
        receipt_epochs.append((result, receipt))
        manifest.append((binding.step_id, receipt[2], receipt[4]))

    stable()
    check_receipts()
    serialized = json.dumps(
        (request_id, plan.schedule_digest, ready, withheld, manifest),
        ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    stable()
    check_receipts()
    fingerprint = hashlib.sha256(_DOMAIN + b"preview\0" + serialized).hexdigest()
    stable()
    check_receipts()
    output = _RESULT_TYPE(
        request_id, plan.schedule_digest, ready, withheld, tuple(results), fingerprint,
    )
    stable()
    check_receipts()
    if (
        type(output) is not _RESULT_TYPE
        or output.request_id is not request_id
        or output.schedule_digest is not plan.schedule_digest
        or output.ready_step_ids is not ready
        or output.withheld_step_ids is not withheld
        or output.fingerprint is not fingerprint
        or output.fixture_results != tuple(results)
    ):
        raise DisconnectedReadToolBridgeRejected("constructed mock preview changed")
    for name in _DENIALS:
        stable()
        check_receipts()
        if getattr(output, name) is not False:
            raise DisconnectedReadToolBridgeRejected("mock preview gained authority")
        check_receipts()
    stable()
    check_receipts()
    return output
