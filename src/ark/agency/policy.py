"""Fail-closed capability and one-shot authorization policy."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import Lock

from .contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from .registry import BoundAction, ToolRegistry

_MAX_GRANTS = 1024  # Bound hostile iterables before WRITE token admission.


class PermissionGate:
    """Exact-scope grant checks with consumable authorization for writes."""

    def __init__(self) -> None:
        self._consumed_tokens: set[str] = set()
        self._token_lock = Lock()  # process-local; never durable approval

    def authorize_registered(
        self,
        registry: ToolRegistry,
        call: ToolCall,
        grants: Iterable[CapabilityGrant],
        *,
        now_ms: int,
        one_shot: OneShotAuthorization | None = None,
    ) -> BoundAction:
        """Opt-in registry-authoritative policy check with NO backend dispatch.

        An untrusted caller cannot downgrade the registry's WRITE effect by
        supplying its own READ ToolSpec. This is a diagnostic authorization
        boundary, not durable one-shot approval or external execution authority.
        """
        if type(registry) is not ToolRegistry or type(call) is not ToolCall:
            raise PermissionDenied("registered authorization requires exact registry and call")
        # The first registry.bind() itself is a caller-controlled callback:
        # pin the original action and token BEFORE entering it. Rebinding
        # twice only establishes consistency with a substituted first input.
        if one_shot is not None and type(one_shot) is not OneShotAuthorization:
            raise PermissionDenied("one-shot authorization must be an exact value")
        try:
            call_epoch = (
                call.tool, call.capability, call.scope,
                call.request_id, call.arguments,
            )
            token_epoch = (
                (one_shot.token_id, one_shot.request_id, one_shot.expires_at_ms)
                if one_shot is not None else None
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise PermissionDenied("registered input identity is invalid") from exc

        def ensure_entry_epoch() -> None:
            try:
                stable = (
                    (call.tool, call.capability, call.scope,
                     call.request_id) == call_epoch[:4]
                    and all(
                        actual is original
                        for actual, original in zip(
                            (call.tool, call.capability, call.scope, call.arguments),
                            (call_epoch[0], call_epoch[1], call_epoch[2], call_epoch[4]),
                            strict=True,
                        )
                    )
                    and (
                        (one_shot.token_id, one_shot.request_id, one_shot.expires_at_ms)
                        if one_shot is not None else None
                    ) == token_epoch
                    and (
                        one_shot is None
                        or one_shot.token_id is token_epoch[0]
                        and one_shot.request_id is token_epoch[1]
                        and one_shot.expires_at_ms is token_epoch[2]
                    )
                )
            except (AttributeError, TypeError, ValueError) as exc:
                raise PermissionDenied("registered input identity changed") from exc
            if not stable:
                raise PermissionDenied("registered input identity changed")

        try:
            bound = registry.bind(call)
            ensure_entry_epoch()
            # Materialize external grant iterables before any WRITE token is
            # spent; they may mutate a reflected ToolCall/registry as they run.
            materialized = []
            original_grants = []

            def ensure_grant_epoch() -> None:
                # Separate grant custody from registry rebinding so a
                # registry-drift error keeps its established diagnostic at
                # the under-lock admission boundary.
                try:
                    stable_grants = all(
                        type(previous) is CapabilityGrant
                        and all(
                            current is original for current, original in zip(
                                (
                                    previous.capability, previous.scope,
                                    previous.expires_at_ms,
                                ),
                                epoch, strict=True,
                            )
                        )
                        for previous, epoch in original_grants
                    )
                except (AttributeError, TypeError, ValueError) as exc:
                    raise PermissionDenied(
                        "registered grant identity changed during materialization"
                    ) from exc
                if not stable_grants:
                    raise PermissionDenied(
                        "registered grant identity changed during materialization"
                    )

            def ensure_materialization_epoch() -> None:
                # Each iterator advance may run arbitrary caller code, then
                # restore the identity before exhaustion. Preserve all
                # previously observed grants and the bound registry revision
                # after every yielded item.
                ensure_entry_epoch()
                try:
                    stable_registry = registry.revision == bound.registry_revision
                except (TypeError, ValueError) as exc:
                    raise PermissionDenied(
                        "registry binding changed during grants"
                    ) from exc
                ensure_entry_epoch()
                if not stable_registry:
                    raise PermissionDenied(
                        "registry binding changed during grants"
                    )
                ensure_grant_epoch()

            for grant in grants:
                ensure_materialization_epoch()
                if len(materialized) >= _MAX_GRANTS:
                    raise PermissionDenied("capability grant budget exceeded")
                if type(grant) is not CapabilityGrant:
                    raise PermissionDenied(
                        "capability grant must be an exact value"
                    )
                original_grants.append((
                    grant, (
                        grant.capability, grant.scope, grant.expires_at_ms,
                    ),
                ))
                materialized.append(grant)
            ensure_materialization_epoch()
            grant_snapshot = tuple(materialized)
            verified = registry.bind(call)
            ensure_entry_epoch()
            # The second bind is another reentrant boundary. Retain the
            # original grants; registry mismatches keep the existing
            # bound-vs-verified identity diagnostic immediately below.
            ensure_grant_epoch()
        except (KeyError, TypeError, ValueError) as exc:
            raise PermissionDenied("registry binding failed before authorization") from exc
        if (
            bound.registry_revision != verified.registry_revision
            or bound.bound_action_id != verified.bound_action_id
            or bound.registration is not verified.registration
            or bound.call is not verified.call
        ):
            raise PermissionDenied("registry identity changed while reading grants")

        registration = verified.registration
        spec = ToolSpec(registration.name, registration.capability, registration.effect)

        def ensure_registered_binding() -> None:
            # WRITE token admission must rebind under the token-spend lock,
            # not merely before potentially contended grant evaluation.
            # Retain the pre-materialization grant epochs at each rebind,
            # including a reflected mutation within the under-lock bind.
            ensure_entry_epoch()
            ensure_grant_epoch()
            try:
                current = registry.bind(call)
                ensure_entry_epoch()
            except (KeyError, TypeError, ValueError) as exc:
                raise PermissionDenied("registered identity changed before spend") from exc
            if (
                current.registry_revision != verified.registry_revision
                or current.bound_action_id != verified.bound_action_id
                or current.registration is not verified.registration
                or current.call is not verified.call
            ):
                raise PermissionDenied("registered identity changed before spend")
            # Keep the original (pre-materialization) grant witnesses through
            # the reentrant registry callback, before token admission.
            ensure_grant_epoch()

        self.authorize(
            spec, call, grant_snapshot, now_ms=now_ms, one_shot=one_shot,
            _registered_recheck=ensure_registered_binding,
        )
        ensure_entry_epoch()
        ensure_registered_binding()
        return verified

    def authorize(
        self,
        spec: ToolSpec,
        call: ToolCall,
        grants: Iterable[CapabilityGrant],
        *,
        now_ms: int,
        one_shot: OneShotAuthorization | None = None,
        _registered_recheck: Callable[[], None] | None = None,
    ) -> None:
        if _registered_recheck is not None and not callable(_registered_recheck):
            raise PermissionDenied("registered recheck must be callable")
        if type(spec) is not ToolSpec or type(call) is not ToolCall:
            raise PermissionDenied("authorization requires exact ToolSpec and ToolCall")
        if one_shot is not None and type(one_shot) is not OneShotAuthorization:
            raise PermissionDenied("one-shot authorization must be an exact value")
        if spec.name != call.tool or spec.capability != call.capability:
            raise PermissionDenied("tool call does not match registered tool specification")
        if type(now_ms) is not int or not 0 <= now_ms <= (1 << 63) - 1:
            raise ValueError("now_ms must be a non-negative integer")

        # A user-supplied grant iterable can execute reentrant Python code.
        # Pin the identity before iteration; no WRITE token may be spent if a
        # reflected frozen value changes during evaluation.
        try:
            spec_epoch = (spec.name, spec.capability, spec.effect)
            call_epoch = (
                call.tool, call.capability, call.scope, call.arguments,
                call.request_id,
            )
            token_epoch = (
                (one_shot.token_id, one_shot.request_id, one_shot.expires_at_ms)
                if one_shot is not None else None
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise PermissionDenied("authorization input identity is invalid") from exc

        def original_field_carriers() -> bool:
            # request_id on ToolCall is a deterministic computed digest, so
            # preserve its VALUE (already checked separately), not the identity
            # of each freshly computed string. Other fields are stored values
            # whose exact original carriers must survive reentrant callbacks.
            return (
                all(
                    current is initial
                    for current, initial in zip(
                        (spec.name, spec.capability, spec.effect),
                        spec_epoch, strict=True,
                    )
                )
                and all(
                    current is initial
                    for current, initial in zip(
                        (call.tool, call.capability, call.scope, call.arguments),
                        call_epoch[:4], strict=True,
                    )
                )
                and (
                    one_shot is None
                    or one_shot.token_id is token_epoch[0]
                    and one_shot.request_id is token_epoch[1]
                    and one_shot.expires_at_ms is token_epoch[2]
                )
            )

        matching = []
        grant_epochs = []

        def assert_iteration_epoch() -> None:
            # A generator can temporarily retarget a previously yielded
            # grant, the action, or a WRITE token, then restore it before
            # StopIteration. The final-only check would miss that intermediate
            # identity and could consume a token for an inconsistent review.
            try:
                stable = (
                    (spec.name, spec.capability, spec.effect) == spec_epoch
                    and (
                        call.tool, call.capability, call.scope,
                        call.arguments, call.request_id,
                    ) == call_epoch
                    and call.arguments is call_epoch[3]
                    and original_field_carriers()
                    and (
                        (
                            one_shot.token_id, one_shot.request_id,
                            one_shot.expires_at_ms,
                        ) if one_shot is not None else None
                    ) == token_epoch
                    and all(
                        type(item) is CapabilityGrant
                        and all(
                            current is original for current, original in zip(
                                (item.capability, item.scope, item.expires_at_ms),
                                epoch, strict=True,
                            )
                        )
                        for item, epoch in grant_epochs
                    )
                )
            except (AttributeError, TypeError, ValueError) as exc:
                raise PermissionDenied(
                    "authorization input changed during grants"
                ) from exc
            if not stable:
                raise PermissionDenied(
                    "authorization input changed during grants"
                )

        for grant in grants:
            assert_iteration_epoch()
            if len(grant_epochs) >= _MAX_GRANTS:
                raise PermissionDenied("capability grant budget exceeded")
            if type(grant) is not CapabilityGrant:
                raise PermissionDenied("capability grant must be an exact value")
            epoch = (grant.capability, grant.scope, grant.expires_at_ms)
            try:
                CapabilityGrant(*epoch)
            except (TypeError, ValueError) as exc:
                raise PermissionDenied("capability grant identity is invalid") from exc
            grant_epochs.append((grant, epoch))
            if (
                grant.capability == call.capability
                and grant.scope == call.scope
                and (grant.expires_at_ms is None or grant.expires_at_ms > now_ms)
            ):
                matching.append(grant)
        try:
            stable = (
                (spec.name, spec.capability, spec.effect) == spec_epoch
                and (
                    call.tool, call.capability, call.scope,
                    call.arguments, call.request_id,
                ) == call_epoch
                and call.arguments is call_epoch[3]
                and original_field_carriers()
                and (
                    (one_shot.token_id, one_shot.request_id, one_shot.expires_at_ms)
                    if one_shot is not None else None
                ) == token_epoch
                and all(
                    type(grant) is CapabilityGrant
                    and all(
                        current is original for current, original in zip(
                            (grant.capability, grant.scope, grant.expires_at_ms),
                            epoch, strict=True,
                        )
                    )
                    for grant, epoch in grant_epochs
                )
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise PermissionDenied("authorization input changed during grants") from exc
        if not stable:
            raise PermissionDenied("authorization input changed during grants")
        if not matching:
            raise PermissionDenied("no active exact-scope capability grant")

        if spec.effect is Effect.WRITE:
            if one_shot is None:
                raise PermissionDenied("write-effect call requires exact one-shot authorization")
            # The membership check and spend must be one critical section.
            # Recheck the token/call epoch after waiting for the lock: a
            # reflected mutation during contention must not spend a token.
            with self._token_lock:
                # The lock may be contended after grant enumeration and the
                # earlier epoch check. Revalidate every policy input before
                # irreversibly spending a process-local token, not just the
                # token itself. A reflected grant/spec mutation must fail shut.
                try:
                    stable_at_spend = (
                        (spec.name, spec.capability, spec.effect) == spec_epoch
                        and (
                            call.tool, call.capability, call.scope,
                            call.arguments, call.request_id,
                        ) == call_epoch
                        and call.arguments is call_epoch[3]
                        and original_field_carriers()
                        and (
                            one_shot.token_id,
                            one_shot.request_id,
                            one_shot.expires_at_ms,
                        ) == token_epoch
                        and all(
                            type(grant) is CapabilityGrant
                            and all(
                                current is original for current, original in zip(
                                    (grant.capability, grant.scope, grant.expires_at_ms),
                                    epoch, strict=True,
                                )
                            )
                            for grant, epoch in grant_epochs
                        )
                    )
                except (AttributeError, TypeError, ValueError) as exc:
                    raise PermissionDenied(
                        "authorization input changed during token spend"
                    ) from exc
                if not stable_at_spend:
                    raise PermissionDenied("authorization input changed during token spend")
                if _registered_recheck is not None:
                    _registered_recheck()
                if one_shot.token_id in self._consumed_tokens:
                    raise PermissionDenied("one-shot authorization was already consumed")
                if one_shot.request_id != call.request_id:
                    raise PermissionDenied("one-shot authorization does not match this request")
                if one_shot.expires_at_ms <= now_ms:
                    raise PermissionDenied("one-shot authorization expired")
                self._consumed_tokens.add(one_shot.token_id)
