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


class PermissionGate:
    """Exact-scope grant checks with consumable authorization for writes."""

    def __init__(self) -> None:
        self._consumed_tokens: set[str] = set()

    def authorize(
        self,
        spec: ToolSpec,
        call: ToolCall,
        grants: Iterable[CapabilityGrant],
        *,
        now_ms: int,
        one_shot: OneShotAuthorization | None = None,
    ) -> None:
        if spec.name != call.tool or spec.capability != call.capability:
            raise PermissionDenied("tool call does not match registered tool specification")
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be a non-negative integer")

        matching = [
            grant
            for grant in grants
            if grant.capability == call.capability
            and grant.scope == call.scope
            and (grant.expires_at_ms is None or grant.expires_at_ms > now_ms)
        ]
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
