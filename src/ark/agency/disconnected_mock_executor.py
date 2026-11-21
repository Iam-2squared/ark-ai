"""Disconnected mock-only composition of registry, permission, occurrence and audit.

This executor accepts only the exact in-process MockToolBackend. It never
opens a network, shell, device, model or arbitrary ToolBackend. Its caller
supplies a synthetic policy time; neither that value nor the local SQLite
ledgers authenticate consent, trusted time, independent custody or an external
effect. Separate occurrence and audit databases are not cross-store atomic.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass

from .audit import SQLiteActionAudit
from .contracts import (
    ActionAuditEvent,
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    ToolCall,
)
from .durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReservationReceipt,
)
from .policy import PermissionGate
from .registry import BoundAction, ToolRegistry

_MAX_INT = 2**63 - 1
_OCCURRENCE = re.compile(r"occ_[0-9a-f]{64}\Z")
_RESULT_DOMAIN = b"ARK-disconnected-mock-result-v1\0"
_PRE_ACTION_OUTCOME = "mock_pre_action"
_COMPLETED_OUTCOME = "mock_completed"
_ORIGINAL_EXECUTOR_CONSTANTS = (
    _MAX_INT, _OCCURRENCE, _RESULT_DOMAIN,
    _PRE_ACTION_OUTCOME, _COMPLETED_OUTCOME,
)
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256


class DisconnectedMockExecutionRejected(RuntimeError):
    """A mock-only execution input or component was inconsistent."""


@dataclass(frozen=True, slots=True)
class MockToolResult:
    request_id: str
    result_sha256: str

    @property
    def external_effect_proven(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class MockExecutionReceipt:
    request_id: str
    registry_revision: str
    bound_action_id: str
    effect: Effect
    occurrence_id: str | None
    pre_action_event_id: int
    completion_event_id: int
    result_sha256: str

    @property
    def mock_only(self) -> bool:
        return True

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_effect_proven(self) -> bool:
        return False

    @property
    def exact_once_external_effect_proven(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False


class MockToolBackend:
    """Deterministic in-process backend; no filesystem, network or device I/O."""

    __slots__ = ("_calls",)

    def __init__(self) -> None:
        self._calls = 0

    @property
    def calls(self) -> int:
        return self._calls

    def execute(self, call: ToolCall) -> MockToolResult:
        if type(self) is not MockToolBackend or type(call) is not ToolCall:
            raise DisconnectedMockExecutionRejected(
                "mock backend requires exact backend and ToolCall"
            )
        if type(self._calls) is not int or self._calls < 0:
            raise DisconnectedMockExecutionRejected("mock backend counter changed")
        request_id = call.request_id
        if type(request_id) is not str or re.fullmatch(
            r"act_[0-9a-f]{64}", request_id,
        ) is None:
            raise DisconnectedMockExecutionRejected("mock request identity is invalid")
        self._calls += 1
        digest = hashlib.sha256(
            _RESULT_DOMAIN + request_id.encode("ascii")
        ).hexdigest()
        return MockToolResult(request_id, digest)


# Pin the only backend implementation and every foundation method this
# composition invokes. Exact object types alone do not prevent instance
# method shadowing or a class-level replacement before registry construction.
_MOCK_BACKEND_TYPE = MockToolBackend
_MOCK_BACKEND_METHODS = (
    "__init__", "execute", "calls", "__new__", "__getattribute__", "__getattr__",
)
_ORIGINAL_MOCK_BACKEND_METHODS = tuple(
    vars(_MOCK_BACKEND_TYPE).get(name) for name in _MOCK_BACKEND_METHODS
)
_MOCK_RESULT_TYPE = MockToolResult
_MOCK_RESULT_FIELDS = ("request_id", "result_sha256", "external_effect_proven")
_MOCK_RESULT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_MOCK_RESULT_MEMBERS = tuple(
    vars(_MOCK_RESULT_TYPE).get(name) for name in _MOCK_RESULT_FIELDS
)
_ORIGINAL_MOCK_RESULT_HOOKS = tuple(
    vars(_MOCK_RESULT_TYPE).get(name) for name in _MOCK_RESULT_HOOKS
)
_ORIGINAL_MOCK_RESULT_INIT = vars(_MOCK_RESULT_TYPE)["__init__"]
_RECEIPT_TYPE = MockExecutionReceipt
_RECEIPT_FIELDS = (
    "request_id", "registry_revision", "bound_action_id", "effect",
    "occurrence_id", "pre_action_event_id", "completion_event_id",
    "result_sha256",
)
_RECEIPT_DENIALS = (
    "mock_only", "dispatch_authorized", "automatic_replay_authorized",
    "external_effect_proven", "exact_once_external_effect_proven",
    "trusted_clock_verified", "independent_custody_proven",
)
_RECEIPT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RECEIPT_MEMBERS = tuple(
    vars(_RECEIPT_TYPE).get(name)
    for name in _RECEIPT_FIELDS + _RECEIPT_DENIALS
)
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_TYPE).get(name) for name in _RECEIPT_HOOKS
)
_ORIGINAL_RECEIPT_INIT = vars(_RECEIPT_TYPE)["__init__"]
_ORIGINAL_MOCK_EXECUTE = vars(_MOCK_BACKEND_TYPE)["execute"]

_ORIGINAL_REGISTRY_BIND = vars(ToolRegistry)["bind"]
_ORIGINAL_REGISTRY_RESOLVE = vars(ToolRegistry)["resolve"]
_ORIGINAL_REGISTRY_GET = vars(ToolRegistry)["get"]
_ORIGINAL_REGISTRY_REVISION = vars(ToolRegistry)["revision"]
_ORIGINAL_REGISTRY_EPOCH = vars(ToolRegistry)["_assert_registration_epoch"]
_ORIGINAL_GATE_REGISTERED = vars(PermissionGate)["authorize_registered"]
_ORIGINAL_GATE_AUTHORIZE = vars(PermissionGate)["authorize"]
_ORIGINAL_AUDIT_APPEND = vars(SQLiteActionAudit)["append"]
_ORIGINAL_AUDIT_CONNECT = vars(SQLiteActionAudit)["_connect"]
_ORIGINAL_AUDIT_NOW = vars(SQLiteActionAudit)["_now"]
_ORIGINAL_OCCURRENCE_RESERVE = vars(SyntheticOccurrenceStore)["reserve_synthetic"]
_ORIGINAL_OCCURRENCE_CONNECT = vars(SyntheticOccurrenceStore)["_connect"]


def _require_original_components(
    registry: ToolRegistry,
    gate: PermissionGate,
    audit: SQLiteActionAudit,
    occurrences: SyntheticOccurrenceStore | None,
) -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or (
            _MAX_INT, _OCCURRENCE, _RESULT_DOMAIN,
            _PRE_ACTION_OUTCOME, _COMPLETED_OUTCOME,
        ) != _ORIGINAL_EXECUTOR_CONSTANTS
    ):
        raise DisconnectedMockExecutionRejected(
            "disconnected mock executor codec or limits changed"
        )
    if (
        MockToolBackend is not _MOCK_BACKEND_TYPE
        or any(
            vars(_MOCK_BACKEND_TYPE).get(name) is not original
            for name, original in zip(
                _MOCK_BACKEND_METHODS, _ORIGINAL_MOCK_BACKEND_METHODS,
                strict=True,
            )
        )
        or MockToolResult is not _MOCK_RESULT_TYPE
        or vars(_MOCK_RESULT_TYPE).get("__init__") is not _ORIGINAL_MOCK_RESULT_INIT
        or any(
            vars(_MOCK_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _MOCK_RESULT_FIELDS, _ORIGINAL_MOCK_RESULT_MEMBERS, strict=True,
            )
        )
        or any(
            vars(_MOCK_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _MOCK_RESULT_HOOKS, _ORIGINAL_MOCK_RESULT_HOOKS, strict=True,
            )
        )
        or MockExecutionReceipt is not _RECEIPT_TYPE
        or vars(_RECEIPT_TYPE).get("__init__") is not _ORIGINAL_RECEIPT_INIT
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _RECEIPT_FIELDS + _RECEIPT_DENIALS,
                _ORIGINAL_RECEIPT_MEMBERS,
                strict=True,
            )
        )
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _RECEIPT_HOOKS, _ORIGINAL_RECEIPT_HOOKS, strict=True,
            )
        )
    ):
        raise DisconnectedMockExecutionRejected(
            "mock backend, result or receipt definition changed"
        )
    if (
        vars(ToolRegistry).get("bind") is not _ORIGINAL_REGISTRY_BIND
        or vars(ToolRegistry).get("resolve") is not _ORIGINAL_REGISTRY_RESOLVE
        or vars(ToolRegistry).get("get") is not _ORIGINAL_REGISTRY_GET
        or vars(ToolRegistry).get("revision") is not _ORIGINAL_REGISTRY_REVISION
        or vars(ToolRegistry).get("_assert_registration_epoch") is not _ORIGINAL_REGISTRY_EPOCH
        or any(name in vars(registry) for name in ("bind", "resolve", "get", "revision"))
    ):
        raise DisconnectedMockExecutionRejected("ToolRegistry method identity changed")
    if (
        vars(PermissionGate).get("authorize_registered") is not _ORIGINAL_GATE_REGISTERED
        or vars(PermissionGate).get("authorize") is not _ORIGINAL_GATE_AUTHORIZE
        or any(name in vars(gate) for name in ("authorize_registered", "authorize"))
    ):
        raise DisconnectedMockExecutionRejected("PermissionGate method identity changed")
    if (
        vars(SQLiteActionAudit).get("append") is not _ORIGINAL_AUDIT_APPEND
        or vars(SQLiteActionAudit).get("_connect") is not _ORIGINAL_AUDIT_CONNECT
        or vars(SQLiteActionAudit).get("_now") is not _ORIGINAL_AUDIT_NOW
        or any(name in vars(audit) for name in ("append", "_connect", "_now"))
    ):
        raise DisconnectedMockExecutionRejected("ActionAudit method identity changed")
    if occurrences is not None and (
        vars(SyntheticOccurrenceStore).get("reserve_synthetic")
        is not _ORIGINAL_OCCURRENCE_RESERVE
        or vars(SyntheticOccurrenceStore).get("_connect") is not _ORIGINAL_OCCURRENCE_CONNECT
        or any(
            name in vars(occurrences)
            for name in ("reserve_synthetic", "_connect")
        )
    ):
        raise DisconnectedMockExecutionRejected(
            "synthetic occurrence store method identity changed"
        )


class DisconnectedMockExecutor:
    """Compose local policy and audit around an exact deterministic mock only.

    WRITE order is: local PermissionGate -> durable synthetic occurrence
    reservation -> pre-action audit commit -> mock backend -> completion audit.
    A failure at any earlier stage prevents the mock call. If a later stage
    fails, callers must inspect local evidence; this class never retries.
    """

    __slots__ = (
        "_registry", "_gate", "_audit", "_occurrences",
        "_registry_revision_epoch", "_audit_path_epoch",
        "_occurrence_path_epoch", "_component_epoch",
    )

    def __init__(
        self,
        registry: ToolRegistry,
        gate: PermissionGate,
        audit: SQLiteActionAudit,
        occurrences: SyntheticOccurrenceStore | None = None,
    ) -> None:
        if (
            type(registry) is not ToolRegistry
            or type(gate) is not PermissionGate
            or type(audit) is not SQLiteActionAudit
            or (
                occurrences is not None
                and type(occurrences) is not SyntheticOccurrenceStore
            )
        ):
            raise TypeError("mock executor requires exact local foundation components")
        _require_original_components(registry, gate, audit, occurrences)
        self._registry = registry
        self._gate = gate
        self._audit = audit
        self._occurrences = occurrences
        self._registry_revision_epoch = registry.revision
        self._audit_path_epoch = audit.path
        self._occurrence_path_epoch = (
            occurrences._path if occurrences is not None else None
        )
        self._component_epoch = (registry, gate, audit, occurrences)

    def _assert_component_epoch(self) -> None:
        registry, gate, audit, occurrences = self._component_epoch
        if (
            self._registry is not registry
            or self._gate is not gate
            or self._audit is not audit
            or self._occurrences is not occurrences
            or self._registry.revision is not self._registry_revision_epoch
            or self._audit.path is not self._audit_path_epoch
            or (
                occurrences is not None
                and occurrences._path is not self._occurrence_path_epoch
            )
        ):
            raise DisconnectedMockExecutionRejected(
                "mock executor component identity changed"
            )
        _require_original_components(registry, gate, audit, occurrences)

    def execute(
        self,
        call: ToolCall,
        grants: Iterable[CapabilityGrant],
        *,
        now_ms: int,
        one_shot: OneShotAuthorization | None = None,
        occurrence_id: str | None = None,
    ) -> MockExecutionReceipt:
        """Run one mock-only operation; now_ms is synthetic, never trusted time."""
        self._assert_component_epoch()
        if type(call) is not ToolCall:
            raise DisconnectedMockExecutionRejected("call must be an exact ToolCall")
        if type(now_ms) is not int or not 0 <= now_ms <= _MAX_INT:
            raise DisconnectedMockExecutionRejected("synthetic time is invalid")
        if one_shot is not None and type(one_shot) is not OneShotAuthorization:
            raise DisconnectedMockExecutionRejected("one-shot value has wrong type")
        if occurrence_id is not None and (
            type(occurrence_id) is not str
            or len(occurrence_id) != 68
            or _OCCURRENCE.fullmatch(occurrence_id) is None
        ):
            raise DisconnectedMockExecutionRejected("occurrence identity is invalid")

        try:
            initial = _ORIGINAL_REGISTRY_BIND(self._registry, call)
        except Exception as exc:
            raise DisconnectedMockExecutionRejected(
                "mock registry binding failed"
            ) from exc
        self._assert_component_epoch()
        if (
            type(initial) is not BoundAction
            or initial.call is not call
            or type(initial.registration.backend) is not _MOCK_BACKEND_TYPE
            or vars(_MOCK_BACKEND_TYPE).get("execute") is not _ORIGINAL_MOCK_EXECUTE
        ):
            raise DisconnectedMockExecutionRejected(
                "only the exact disconnected MockToolBackend is accepted"
            )
        backend = initial.registration.backend
        effect = initial.registration.effect
        if type(effect) is not Effect:
            raise DisconnectedMockExecutionRejected("registered effect is invalid")
        if effect is Effect.READ:
            if one_shot is not None or occurrence_id is not None:
                raise DisconnectedMockExecutionRejected(
                    "READ mock calls do not accept WRITE occurrence inputs"
                )
        elif effect is Effect.WRITE:
            if one_shot is None or occurrence_id is None:
                raise DisconnectedMockExecutionRejected(
                    "WRITE mock calls require a one-shot token and occurrence ID"
                )
            if self._occurrences is None:
                raise DisconnectedMockExecutionRejected(
                    "WRITE mock calls require a durable local occurrence store"
                )
        else:
            raise DisconnectedMockExecutionRejected("registered effect is unsupported")

        try:
            authorized = _ORIGINAL_GATE_REGISTERED(
                self._gate,
                self._registry,
                call,
                grants,
                now_ms=now_ms,
                one_shot=one_shot,
            )
        except Exception as exc:
            raise DisconnectedMockExecutionRejected(
                "local PermissionGate denied the mock operation"
            ) from exc
        self._assert_component_epoch()
        if (
            type(authorized) is not BoundAction
            or authorized.call is not call
            or authorized.registration is not initial.registration
            or authorized.registry_revision != initial.registry_revision
            or authorized.bound_action_id != initial.bound_action_id
            or type(authorized.registration.backend) is not _MOCK_BACKEND_TYPE
            or authorized.registration.backend is not backend
        ):
            raise DisconnectedMockExecutionRejected(
                "registered action identity changed during authorization"
            )

        if effect is Effect.WRITE:
            assert self._occurrences is not None
            try:
                reservation = _ORIGINAL_OCCURRENCE_RESERVE(
                    self._occurrences,
                    self._registry,
                    call,
                    one_shot,
                    occurrence_id=occurrence_id,
                    now_ms=now_ms,
                )
            except Exception as exc:
                raise DisconnectedMockExecutionRejected(
                    "durable synthetic occurrence reservation failed"
                ) from exc
            self._assert_component_epoch()
            if (
                type(reservation) is not SyntheticReservationReceipt
                or reservation.occurrence_id != occurrence_id
                or reservation.request_id != call.request_id
                or reservation.dispatch_authorized is not False
                or reservation.automatic_replay_authorized is not False
            ):
                raise DisconnectedMockExecutionRejected(
                    "synthetic occurrence receipt is malformed or authorizing"
                )

        # This commit is a hard gate: if audit append fails, execute is never
        # called. The audit and occurrence databases remain separate stores.
        try:
            pre_action = _ORIGINAL_AUDIT_APPEND(
                self._audit, call, outcome=_PRE_ACTION_OUTCOME,
            )
        except Exception as exc:
            raise DisconnectedMockExecutionRejected(
                "pre-action audit failed; mock backend was not called"
            ) from exc
        self._assert_component_epoch()
        if (
            type(pre_action) is not ActionAuditEvent
            or pre_action.request_id != call.request_id
            or pre_action.outcome != _PRE_ACTION_OUTCOME
            or type(pre_action.event_id) is not int
            or pre_action.event_id < 1
        ):
            raise DisconnectedMockExecutionRejected(
                "pre-action audit receipt is inconsistent"
            )

        # Rebind after the audit callback and immediately before the only
        # dispatch point. A changed registry or call cannot reach the mock.
        try:
            final = _ORIGINAL_REGISTRY_BIND(self._registry, call)
        except Exception as exc:
            raise DisconnectedMockExecutionRejected(
                "mock binding changed after pre-action audit"
            ) from exc
        self._assert_component_epoch()
        if (
            type(final) is not BoundAction
            or final.call is not call
            or final.registration is not initial.registration
            or final.registry_revision != initial.registry_revision
            or final.bound_action_id != initial.bound_action_id
            or final.registration.backend is not backend
            or type(final.registration.backend) is not _MOCK_BACKEND_TYPE
        ):
            raise DisconnectedMockExecutionRejected(
                "mock action identity changed before backend call"
            )

        result = _ORIGINAL_MOCK_EXECUTE(backend, call)
        self._assert_component_epoch()
        if (
            type(result) is not _MOCK_RESULT_TYPE
            or result.request_id != call.request_id
            or type(result.result_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", result.result_sha256) is None
            or result.external_effect_proven is not False
        ):
            raise DisconnectedMockExecutionRejected(
                "mock backend returned an invalid result"
            )

        try:
            completed = _ORIGINAL_AUDIT_APPEND(
                self._audit, call, outcome=_COMPLETED_OUTCOME,
            )
        except Exception as exc:
            # The mock already ran. Do not retry or claim that the completion
            # audit can retroactively undo it. No real external effect exists.
            raise DisconnectedMockExecutionRejected(
                "completion audit failed after mock-only execution"
            ) from exc
        self._assert_component_epoch()
        if (
            type(completed) is not ActionAuditEvent
            or completed.request_id != call.request_id
            or completed.outcome != _COMPLETED_OUTCOME
            or type(completed.event_id) is not int
            or completed.event_id <= pre_action.event_id
        ):
            raise DisconnectedMockExecutionRejected(
                "completion audit receipt is inconsistent"
            )

        return MockExecutionReceipt(
            request_id=call.request_id,
            registry_revision=initial.registry_revision,
            bound_action_id=initial.bound_action_id,
            effect=effect,
            occurrence_id=occurrence_id,
            pre_action_event_id=pre_action.event_id,
            completion_event_id=completed.event_id,
            result_sha256=result.result_sha256,
        )


__all__ = [
    "DisconnectedMockExecutionRejected",
    "DisconnectedMockExecutor",
    "MockExecutionReceipt",
    "MockToolBackend",
    "MockToolResult",
]
