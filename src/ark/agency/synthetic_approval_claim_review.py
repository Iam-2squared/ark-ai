"""Registry-bound approval *claim* review for disconnected WRITE fixtures.

No issuer, subject, purpose, recipient, clock, nonce, or revocation set here is
authenticated. Matching digests are NOT human consent, a grant, or authority to
dispatch a ToolBackend. This module does not execute a backend.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .contracts import Effect, ToolCall
from .registry import ToolRegistry

_MAX = 2**63 - 1
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_APPROVAL = re.compile(r"approval_[0-9a-f]{64}\Z")
_REGISTRY = re.compile(r"tools_[0-9a-f]{64}\Z")
_BOUND = re.compile(r"bound_[0-9a-f]{64}\Z")
_REQUEST = re.compile(r"act_[0-9a-f]{64}\Z")


class SyntheticApprovalRejected(RuntimeError):
    """A synthetic, unauthenticated approval claim cannot be reconciled."""


@dataclass(frozen=True, slots=True)
class SyntheticApprovalEnvelope:
    approval_id: str
    registry_revision: str
    bound_action_id: str
    request_id: str
    issuer_digest: str
    subject_digest: str
    purpose_digest: str
    recipient_digest: str
    nonce_digest: str
    issued_at_ms: int
    expires_at_ms: int

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def human_consent_verified(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SyntheticApprovalReview:
    approval_id: str
    bound_action_id: str
    observed_at_ms: int

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def human_consent_verified(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


def _identity(fields: tuple[object, ...]) -> str:
    encoded = json.dumps(
        ["ARK-untrusted-approval-claim-v1", *fields],
        ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return "approval_" + hashlib.sha256(encoded).hexdigest()


def _fields(value: SyntheticApprovalEnvelope) -> tuple[object, ...]:
    return (
        value.registry_revision, value.bound_action_id, value.request_id,
        value.issuer_digest, value.subject_digest, value.purpose_digest,
        value.recipient_digest, value.nonce_digest, value.issued_at_ms,
        value.expires_at_ms,
    )


def _validate(value: SyntheticApprovalEnvelope) -> None:
    if (
        type(value.approval_id) is not str or not _APPROVAL.fullmatch(value.approval_id)
        or type(value.registry_revision) is not str
        or not _REGISTRY.fullmatch(value.registry_revision)
        or type(value.bound_action_id) is not str or not _BOUND.fullmatch(value.bound_action_id)
        or type(value.request_id) is not str or not _REQUEST.fullmatch(value.request_id)
        or any(
            type(item) is not str or not _DIGEST.fullmatch(item)
            for item in (
                value.issuer_digest, value.subject_digest, value.purpose_digest,
                value.recipient_digest, value.nonce_digest,
            )
        )
        or type(value.issued_at_ms) is not int
        or type(value.expires_at_ms) is not int
        or not 0 <= value.issued_at_ms < value.expires_at_ms <= _MAX
        or value.approval_id != _identity(_fields(value))
    ):
        raise SyntheticApprovalRejected("synthetic approval claim is malformed or modified")


def make_synthetic_approval_claim(
    registry: ToolRegistry,
    call: ToolCall,
    *,
    issuer_digest: str,
    subject_digest: str,
    purpose_digest: str,
    recipient_digest: str,
    nonce_digest: str,
    issued_at_ms: int,
    expires_at_ms: int,
) -> SyntheticApprovalEnvelope:
    """Create a content-minimized claim for testing; NOT an approval issuer."""
    if type(registry) is not ToolRegistry or type(call) is not ToolCall:
        raise SyntheticApprovalRejected("exact synthetic registry and call required")
    claims = (
        issuer_digest, subject_digest, purpose_digest, recipient_digest,
        nonce_digest, issued_at_ms, expires_at_ms,
    )
    if (
        any(type(item) is not str or not _DIGEST.fullmatch(item) for item in claims[:5])
        or any(type(item) is not int for item in claims[5:])
        or not 0 <= issued_at_ms < expires_at_ms <= _MAX
    ):
        raise SyntheticApprovalRejected("invalid synthetic claim or validity window")
    try:
        bound = registry.bind(call)
        if bound.registration.effect is not Effect.WRITE:
            raise SyntheticApprovalRejected("only WRITE claims may be modeled")
        fields = (
            bound.registry_revision, bound.bound_action_id, bound.call.request_id,
            *claims,
        )
        if registry.bind(call).bound_action_id != bound.bound_action_id:
            raise SyntheticApprovalRejected("registry changed during claim construction")
        claim = SyntheticApprovalEnvelope(_identity(fields), *fields)
        _validate(claim)
        return claim
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise SyntheticApprovalRejected("synthetic binding was rejected") from exc


def review_synthetic_approval_claim(
    envelope: SyntheticApprovalEnvelope,
    registry: ToolRegistry,
    call: ToolCall,
    *,
    issuer_digest: str,
    subject_digest: str,
    purpose_digest: str,
    recipient_digest: str,
    now_ms: int,
    cancelled_ids: frozenset[str],
) -> SyntheticApprovalReview:
    """Check local claim coherence and cancellation; grant ZERO permissions.

    Cancellation is only a caller-supplied set. Absence from this set does
    NOT establish authentic user approval or durable non-revocation.
    """
    if (
        type(envelope) is not SyntheticApprovalEnvelope
        or type(registry) is not ToolRegistry or type(call) is not ToolCall
        or type(now_ms) is not int or not 0 <= now_ms <= _MAX
        or type(cancelled_ids) is not frozenset
        or any(type(item) is not str or not _APPROVAL.fullmatch(item) for item in cancelled_ids)
    ):
        raise SyntheticApprovalRejected("exact synthetic review inputs required")
    expected = (issuer_digest, subject_digest, purpose_digest, recipient_digest)
    if any(type(item) is not str or not _DIGEST.fullmatch(item) for item in expected):
        raise SyntheticApprovalRejected("synthetic reviewers must supply canonical digests")
    _validate(envelope)
    epoch = (envelope.approval_id, _fields(envelope))
    if envelope.approval_id in cancelled_ids:
        raise SyntheticApprovalRejected("synthetic approval claim was cancelled")
    if not envelope.issued_at_ms <= now_ms < envelope.expires_at_ms:
        raise SyntheticApprovalRejected("synthetic claim is not current")
    if expected != (
        envelope.issuer_digest, envelope.subject_digest,
        envelope.purpose_digest, envelope.recipient_digest,
    ):
        raise SyntheticApprovalRejected("synthetic claim actor, purpose or recipient differs")
    try:
        bound = registry.bind(call)
        if bound.registration.effect is not Effect.WRITE or (
            bound.registry_revision, bound.bound_action_id, bound.call.request_id
        ) != (
            envelope.registry_revision, envelope.bound_action_id, envelope.request_id
        ):
            raise SyntheticApprovalRejected("synthetic registry/action binding differs")
        _validate(envelope)
        if (envelope.approval_id, _fields(envelope)) != epoch:
            raise SyntheticApprovalRejected("synthetic claim changed during review")
        again = registry.bind(call)
        if (
            again.registration is not bound.registration
            or again.call is not bound.call
            or again.bound_action_id != bound.bound_action_id
            or (envelope.approval_id, _fields(envelope)) != epoch
        ):
            raise SyntheticApprovalRejected("synthetic registry or claim changed during review")
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise SyntheticApprovalRejected("synthetic approval binding invalid") from exc
    return SyntheticApprovalReview(envelope.approval_id, envelope.bound_action_id, now_ms)
