"""Fail-closed capability and one-shot authorization policy."""

from __future__ import annotations

from collections.abc import Iterable

from .contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from .registry import BoundAction, ToolRegistry


class PermissionGate:
    """Exact-scope grant checks with consumable authorization for writes."""

    def __init__(self) -> None:
        self._consumed_tokens: set[str] = set()

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
        try:
            bound = registry.bind(call)
            # Materialize external grant iterables before any WRITE token is
            # spent; they may mutate a reflected ToolCall/registry as they run.
            grant_snapshot = tuple(grants)
            verified = registry.bind(call)
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
        self.authorize(spec, call, grant_snapshot, now_ms=now_ms, one_shot=one_shot)
        return verified

    def authorize(
        self,
        spec: ToolSpec,
        call: ToolCall,
        grants: Iterable[CapabilityGrant],
        *,
        now_ms: int,
        one_shot: OneShotAuthorization | None = None,
    ) -> None:
        if type(spec) is not ToolSpec or type(call) is not ToolCall:
            raise PermissionDenied("authorization requires exact ToolSpec and ToolCall")
        if one_shot is not None and type(one_shot) is not OneShotAuthorization:
            raise PermissionDenied("one-shot authorization must be an exact value")
        if spec.name != call.tool or spec.capability != call.capability:
            raise PermissionDenied("tool call does not match registered tool specification")
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be a non-negative integer")

        # Evaluate the entire grant stream before deciding; never authorize from
        # a matching record while ignoring an invalid later record.
        matching = []
        for grant in grants:
            if type(grant) is not CapabilityGrant:
                raise PermissionDenied("capability grant must be an exact value")
            if (
                grant.capability == call.capability
                and grant.scope == call.scope
                and (grant.expires_at_ms is None or grant.expires_at_ms > now_ms)
            ):
                matching.append(grant)
        if not matching:
            raise PermissionDenied("no active exact-scope capability grant")

        if spec.effect is Effect.WRITE:
            if one_shot is None:
                raise PermissionDenied("write-effect call requires exact one-shot authorization")
            if one_shot.token_id in self._consumed_tokens:
                raise PermissionDenied("one-shot authorization was already consumed")
            if one_shot.request_id != call.request_id:
                raise PermissionDenied("one-shot authorization does not match this request")
            if one_shot.expires_at_ms <= now_ms:
                raise PermissionDenied("one-shot authorization expired")
            self._consumed_tokens.add(one_shot.token_id)
