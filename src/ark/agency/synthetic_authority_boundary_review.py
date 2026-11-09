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


# These detached claim/observation/report dataclasses are reflection-mutable
# even when frozen. Reject forged getters, initializers or authority-denial
# properties before private claims are read or a report is constructed.
_CLAIMS_TYPE = SyntheticAuthorityClaims
_OBSERVATIONS_TYPE = SyntheticAuthorityObservations
_REPORT_TYPE = SyntheticAuthorityGapReport
_CLAIM_FIELDS = (
    "issuer_claim", "subject_claim", "registry_revision", "bound_action_id",
    "occurrence_digest", "issued_at_ms", "expires_at_ms",
)
_OBSERVATION_FIELDS = (
    "issuer_signature", "trusted_clock", "human_consent",
    "preaction_audit", "occurrence_replay_fence", "external_result",
)
_REPORT_FIELDS = ("claim_digest", "blockers")
_REPORT_DENIALS = (
    "issuer_authenticated", "clock_authenticated",
    "human_consent_verified", "dispatch_authorized",
    "automatic_replay_authorized", "external_outcome_known",
)
_LOOKUP_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_CONTRACTS = (
    (_CLAIMS_TYPE, _CLAIM_FIELDS + _LOOKUP_HOOKS),
    (_OBSERVATIONS_TYPE, _OBSERVATION_FIELDS + _LOOKUP_HOOKS),
    (_REPORT_TYPE, _REPORT_FIELDS + _REPORT_DENIALS + _LOOKUP_HOOKS),
)
_ORIGINAL_CONTRACTS = tuple(
    tuple(vars(cls).get(field) for field in names)
    for cls, names in _CONTRACTS
)


# These inputs are caller-supplied diagnostic claims, not authorization.  A
# substituted digest/JSON implementation or regex can observe private labels
# before any post-hash carrier check.  Pin the exact import-time authorities.
_ORIGINAL_HASHLIB_MODULE = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_MODULE = json
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_FORMATS = (_HEX, _ID, _BOUND, _REGISTRY)
_ORIGINAL_STATES = _STATES
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_MAX_MS = _MAX_MS


def _require_original_authority_dependencies() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB_MODULE
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON_MODULE
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or any(current is not original for current, original in zip(
            (_HEX, _ID, _BOUND, _REGISTRY), _ORIGINAL_FORMATS, strict=True,
        ))
        or _STATES is not _ORIGINAL_STATES
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _MAX_MS is not _ORIGINAL_MAX_MS
    ):
        raise SyntheticAuthorityRejected(
            "synthetic authority digest or parser dependencies changed"
        )



def _require_original_authority_contracts() -> None:
    if (
        SyntheticAuthorityClaims is not _CLAIMS_TYPE
        or SyntheticAuthorityObservations is not _OBSERVATIONS_TYPE
        or SyntheticAuthorityGapReport is not _REPORT_TYPE
        or any(
            vars(cls).get(name) is not original
            for (cls, names), originals in zip(
                _CONTRACTS, _ORIGINAL_CONTRACTS, strict=True,
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticAuthorityRejected(
            "synthetic authority constructor or field hooks changed"
        )


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
    _require_original_authority_dependencies()
    _require_original_authority_contracts()
    if (
        type(claims) is not SyntheticAuthorityClaims
        or type(observations) is not SyntheticAuthorityObservations
        or retained_claim_digest is not None
        and (type(retained_claim_digest) is not str
             or _HEX.fullmatch(retained_claim_digest) is None)
    ):
        raise SyntheticAuthorityRejected("exact synthetic authority types required")
    _require_original_authority_contracts()
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
        _require_original_authority_dependencies()
        _require_original_authority_contracts()
        if (
            type(claims) is not _CLAIMS_TYPE
            or type(observations) is not _OBSERVATIONS_TYPE
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
    _require_original_authority_dependencies()
    _require_original_authority_contracts()
    result = _REPORT_TYPE(digest, blockers)
    _require_original_authority_contracts()
    assert_epoch()
    if (
        type(result) is not _REPORT_TYPE
        or result.claim_digest is not digest
        or result.blockers is not blockers
    ):
        raise SyntheticAuthorityRejected("constructed authority report changed")
    for flag in _REPORT_DENIALS:
        _require_original_authority_contracts()
        if getattr(result, flag) is not False:
            raise SyntheticAuthorityRejected("synthetic authority report gained power")
        _require_original_authority_contracts()
        assert_epoch()
    return result
