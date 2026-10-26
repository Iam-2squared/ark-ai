"""Deny-only, untrusted authority-gap review for disconnected ARK fixtures.

Caller-provided identifiers, local digests and mock verifier observations are
NOT identity, signed time, consent or external action attestation. This code
never grants execution, replay, promotion, or any real-world authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_BOUND = re.compile(r"bound_[0-9a-f]{64}\Z")
_REGISTRY = re.compile(r"tools_[0-9a-f]{64}\Z")
_STATES = frozenset(("absent", "unknown", "caller_claimed"))
_MAX_MS = 2**63 - 1
_DOMAIN = b"ARK-synthetic-authority-gap-v1\0"


class SyntheticAuthorityRejected(ValueError):
    """Malformed or altered synthetic authority observations."""


@dataclass(frozen=True, slots=True)
class SyntheticAuthorityClaims:
    issuer_claim: str
    subject_claim: str
    registry_revision: str
    bound_action_id: str
    occurrence_digest: str
    issued_at_ms: int
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class SyntheticAuthorityObservations:
    issuer_signature: str
    trusted_clock: str
    human_consent: str
    preaction_audit: str
    occurrence_replay_fence: str
    external_result: str


@dataclass(frozen=True, slots=True)
class SyntheticAuthorityGapReport:
    claim_digest: str
    blockers: tuple[str, ...]

    @property
    def issuer_authenticated(self) -> bool:
        return False

    @property
    def clock_authenticated(self) -> bool:
        return False

    @property
    def human_consent_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def review_synthetic_authority_gaps(
    claims: SyntheticAuthorityClaims,
    observations: SyntheticAuthorityObservations,
    *,
    retained_claim_digest: str | None = None,
) -> SyntheticAuthorityGapReport:
    """Classify missing proof; even all 'caller_claimed' cannot release a WRITE.

    A separately retained digest can expose accidental drift, but an untrusted
    caller can fabricate or recalculate it. Proof requires independent trusted
    verification not supplied by this module.
    """
    if (
        type(claims) is not SyntheticAuthorityClaims
        or type(observations) is not SyntheticAuthorityObservations
        or retained_claim_digest is not None
        and (type(retained_claim_digest) is not str
             or _HEX.fullmatch(retained_claim_digest) is None)
    ):
        raise SyntheticAuthorityRejected("exact synthetic authority types required")
    epoch = (
        claims.issuer_claim, claims.subject_claim, claims.registry_revision,
        claims.bound_action_id, claims.occurrence_digest,
        claims.issued_at_ms, claims.expires_at_ms,
    )
    probe = (
        observations.issuer_signature, observations.trusted_clock,
        observations.human_consent, observations.preaction_audit,
        observations.occurrence_replay_fence, observations.external_result,
    )
    if (
        any(type(value) is not str or _ID.fullmatch(value) is None for value in epoch[:2])
        or type(epoch[2]) is not str or _REGISTRY.fullmatch(epoch[2]) is None
        or type(epoch[3]) is not str or _BOUND.fullmatch(epoch[3]) is None
        or type(epoch[4]) is not str or _HEX.fullmatch(epoch[4]) is None
        or any(type(value) is not int or not 0 <= value <= _MAX_MS for value in epoch[5:])
        or epoch[5] >= epoch[6]
        or any(type(value) is not str or value not in _STATES for value in probe)
    ):
        raise SyntheticAuthorityRejected("malformed synthetic authority evidence")

    def assert_epoch() -> None:
        if (
            type(claims) is not SyntheticAuthorityClaims
            or type(observations) is not SyntheticAuthorityObservations
        ):
            raise SyntheticAuthorityRejected("synthetic authority carrier changed")
        if any(
            getattr(claims, key) is not value
            for key, value in zip(
                ("issuer_claim", "subject_claim", "registry_revision",
                 "bound_action_id", "occurrence_digest", "issued_at_ms", "expires_at_ms"),
                epoch, strict=True,
            )
        ) or any(
            getattr(observations, key) is not value
            for key, value in zip(
                ("issuer_signature", "trusted_clock", "human_consent",
                 "preaction_audit", "occurrence_replay_fence", "external_result"),
                probe, strict=True,
            )
        ):
            raise SyntheticAuthorityRejected("synthetic authority carrier changed")

    assert_epoch()
    data = json.dumps(
        [list(epoch), list(probe)], separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    assert_epoch()
    if len(data) > 4096:
        raise SyntheticAuthorityRejected("synthetic authority budget exceeded")
    digest = hashlib.sha256(_DOMAIN + data).hexdigest()
    assert_epoch()
    if retained_claim_digest is not None and digest != retained_claim_digest:
        raise SyntheticAuthorityRejected("retained synthetic claim digest differs")
    blockers = tuple(
        f"{field}_{'not_observed' if state == 'absent' else 'unverified'}"
        for field, state in zip(
            ("issuer_signature", "trusted_clock", "human_consent",
             "preaction_audit", "occurrence_replay_fence", "external_result"),
            probe, strict=True,
        )
    )
    result = SyntheticAuthorityGapReport(digest, blockers)
    assert_epoch()
    if (
        type(result) is not SyntheticAuthorityGapReport
        or result.claim_digest is not digest
        or result.blockers is not blockers
    ):
        raise SyntheticAuthorityRejected("constructed authority report changed")
    return result
