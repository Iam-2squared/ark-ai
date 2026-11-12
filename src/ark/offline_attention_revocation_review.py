"""Read-only privacy-veto bridge for synthetic proactive attention.

The revocation ledger is queried before the attention evaluator. A present
scope veto suppresses further candidate analysis, even for a previously valid
local attention preview. An absent marker does NOT establish consent, delivery
authority, trusted time, cross-store atomicity, or an independently verified
identity. No notification, timer, ToolBackend, or personal text is touched.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import personal_context_revocation_continuity_review as continuity
from . import proactive_attention_preview as attention
from .personal_context_revocation_review import SyntheticContextRevocationLedger

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-offline-attention-revocation-v1\0"
_POLICY = attention.AttentionBudgetPolicy
_MARKER = attention.SyntheticSurfaceMarker
_PREVIEW = attention.AttentionBudgetPreview
_WITNESS = continuity.SyntheticRevocationWitness
_LEDGER = SyntheticContextRevocationLedger
_ATTENTION_REVIEW = attention.preview_proactive_attention
_REVOCATION_REVIEW = continuity.review_revocation_continuity
_DENIALS = (
    "notification_authorized", "consent_verified", "trusted_clock_verified",
    "automatic_replay_authorized", "tool_execution_authorized",
)


class AttentionRevocationRejected(ValueError):
    """The private attention veto review cannot be safely reproduced."""


@dataclass(frozen=True, slots=True)
class AttentionRevocationReview:
    scope_sha256: str
    revocation_witness_id: str
    revocation_count: int
    vetoed: bool
    attention_disposition: str
    attention_review_sha256: str | None
    review_sha256: str

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


_RESULT = AttentionRevocationReview
_ORIGINAL_DENIALS = tuple(vars(_RESULT)[name] for name in _DENIALS)
# Replacing an output field/constructor or digest callback can execute code
# before an otherwise False-only privacy result is checked. Pin originals at
# import rather than trusting a per-call snapshot of executable descriptors.
_RESULT_INPUT_FIELDS = (
    "scope_sha256", "revocation_witness_id", "revocation_count", "vetoed",
    "attention_disposition", "attention_review_sha256", "review_sha256",
)
_RESULT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_CARRIER = tuple(
    vars(_RESULT).get(name) for name in (*_RESULT_INPUT_FIELDS, *_RESULT_HOOKS)
)
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_SHA_PATTERN = _SHA


def review_offline_attention_revocation(
    ledger: SyntheticContextRevocationLedger,
    retained: continuity.SyntheticRevocationWitness,
    policy: attention.AttentionBudgetPolicy,
    history: tuple[attention.SyntheticSurfaceMarker, ...],
    *,
    occurrence_sha256: str,
    observation_sha256: str,
    observed_now_ms: int,
) -> AttentionRevocationReview:
    """Reconcile a retained local veto prefix before any attention evaluation.

    A prior witness must be held outside the ledger by the caller. This
    function only diagnoses a local veto; even REVIEW_ONLY never grants use.
    """
    def original_authorities() -> None:
        if (
            hashlib is not _ORIGINAL_HASHLIB
            or json is not _ORIGINAL_JSON
            or hashlib.sha256 is not _ORIGINAL_SHA256
            or json.dumps is not _ORIGINAL_DUMPS
            or _DOMAIN is not _ORIGINAL_DOMAIN
            or _SHA is not _ORIGINAL_SHA_PATTERN
            or attention.AttentionBudgetPolicy is not _POLICY
            or attention.SyntheticSurfaceMarker is not _MARKER
            or attention.AttentionBudgetPreview is not _PREVIEW
            or attention.preview_proactive_attention is not _ATTENTION_REVIEW
            or continuity.SyntheticRevocationWitness is not _WITNESS
            or continuity.review_revocation_continuity is not _REVOCATION_REVIEW
            or AttentionRevocationReview is not _RESULT
            or any(
                vars(_RESULT).get(name) is not old
                for name, old in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
            )
        ):
            raise AttentionRevocationRejected("original attention/veto authority changed")
        if any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(
                (*_RESULT_INPUT_FIELDS, *_RESULT_HOOKS),
                _ORIGINAL_RESULT_CARRIER, strict=True,
            )
        ):
            raise AttentionRevocationRejected("attention/veto report gained authority")

    original_authorities()
    if (
        type(ledger) is not _LEDGER
        or type(retained) is not _WITNESS
        or type(policy) is not _POLICY
        or type(history) is not tuple or len(history) > 256
        or any(type(row) is not _MARKER for row in history)
        or any(type(value) is not str or _SHA.fullmatch(value) is None
               for value in (policy.scope_sha256, policy.trigger_sha256,
                             occurrence_sha256, observation_sha256))
        or type(observed_now_ms) is not int
        or not 0 <= observed_now_ms < 2**63
    ):
        raise AttentionRevocationRejected("exact bounded attention/veto inputs required")

    source = ledger.path
    policy_epoch = (
        policy.scope_sha256, policy.trigger_sha256, policy.cooldown_ms,
        policy.rolling_window_ms, policy.max_surfaced_per_window,
        policy.suppress_unchanged,
    )
    history_rows = tuple(history)
    history_epoch = tuple((
        row.scope_sha256, row.trigger_sha256, row.occurrence_sha256,
        row.observation_sha256, row.surfaced_at_ms,
    ) for row in history)
    retained_epoch = (retained.rows, retained.witness_id)
    retained_rows = tuple(retained.rows)

    def stable() -> None:
        original_authorities()
        if (
            ledger.path is not source
            or type(retained) is not _WITNESS
            or retained.rows is not retained_epoch[0]
            or retained.witness_id is not retained_epoch[1]
            or type(retained.rows) is not tuple
            or len(retained.rows) != len(retained_rows)
            or any(a is not b for a, b in zip(
                retained.rows, retained_rows, strict=True,
            ))
            or type(policy) is not _POLICY
            or any(a is not b for a, b in zip((
                policy.scope_sha256, policy.trigger_sha256, policy.cooldown_ms,
                policy.rolling_window_ms, policy.max_surfaced_per_window,
                policy.suppress_unchanged,
            ), policy_epoch, strict=True))
            or type(history) is not tuple or len(history) != len(history_rows)
            or any(
                type(row) is not _MARKER or row is not original
                or any(a is not b for a, b in zip((
                    row.scope_sha256, row.trigger_sha256, row.occurrence_sha256,
                    row.observation_sha256, row.surfaced_at_ms,
                ), fields, strict=True))
                for row, original, fields in zip(
                    history, history_rows, history_epoch, strict=True,
                )
            )
        ):
            raise AttentionRevocationRejected("attention/veto evidence changed during review")

    stable()
    # Read the durable veto first; never evaluate candidate history for a
    # locally revoked scope. The scan also rechecks the retained prefix.
    try:
        observed = _REVOCATION_REVIEW(ledger, retained=retained)
    except Exception as exc:
        raise AttentionRevocationRejected("local revocation continuity unavailable") from exc
    stable()
    if type(observed) is not _WITNESS:
        raise AttentionRevocationRejected("exact observed veto witness required")
    witness_epoch = (observed.rows, observed.witness_id)
    try:
        observed.assert_integrity()
    except Exception as exc:
        raise AttentionRevocationRejected("observed veto witness is invalid") from exc
    stable()
    if observed.rows is not witness_epoch[0] or observed.witness_id is not witness_epoch[1]:
        raise AttentionRevocationRejected("observed veto witness changed")

    vetoed = any(digest == policy_epoch[0] for digest, _ in observed.rows)
    if vetoed:
        disposition = "LOCAL_REVOCATION_VETO"
        attention_digest = None
    else:
        try:
            preview = _ATTENTION_REVIEW(
                policy, history, occurrence_sha256=occurrence_sha256,
                observation_sha256=observation_sha256,
                observed_now_ms=observed_now_ms,
            )
        except attention.AttentionPreviewRejected as exc:
            raise AttentionRevocationRejected("synthetic attention review rejected") from exc
        stable()
        if (
            type(preview) is not _PREVIEW
            or any(getattr(preview, name) is not False for name in (
                "notification_authorized", "action_authorized",
                "trusted_clock_verified", "consent_verified",
            ))
        ):
            raise AttentionRevocationRejected("attention preview claimed authority")
        disposition = preview.disposition
        attention_digest = preview.review_sha256
        if (
            type(disposition) is not str
            or type(attention_digest) is not str
            or _SHA.fullmatch(attention_digest) is None
        ):
            raise AttentionRevocationRejected("attention receipt malformed")
    stable()
    if observed.rows is not witness_epoch[0] or observed.witness_id is not witness_epoch[1]:
        raise AttentionRevocationRejected("observed veto witness changed")
    if not vetoed:
        # A revocation can be appended while an otherwise valid detached
        # attention preview runs. A second, retained-prefix-fenced local read
        # refuses to return the earlier REVIEW_ONLY conclusion under a newly
        # observed veto. This is NOT an atomic cross-store consent check.
        try:
            final_veto = _REVOCATION_REVIEW(ledger, retained=observed)
        except Exception as exc:
            raise AttentionRevocationRejected(
                "local revocation changed during attention review"
            ) from exc
        stable()
        if (
            type(final_veto) is not _WITNESS
            or final_veto.rows != witness_epoch[0]
            or final_veto.witness_id != witness_epoch[1]
            or observed.rows is not witness_epoch[0]
            or observed.witness_id is not witness_epoch[1]
        ):
            raise AttentionRevocationRejected(
                "local revocation changed during attention review"
            )
    payload = (
        policy_epoch[:2], occurrence_sha256, observation_sha256, observed_now_ms,
        observed.witness_id, len(observed.rows), vetoed,
        disposition, attention_digest,
    )
    digest = hashlib.sha256(
        _DOMAIN + json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()
    stable()
    result = _RESULT(
        policy.scope_sha256, observed.witness_id, len(observed.rows),
        vetoed, disposition, attention_digest, digest,
    )
    result_epoch = (
        result.scope_sha256, result.revocation_witness_id,
        result.revocation_count, result.vetoed, result.attention_disposition,
        result.attention_review_sha256, result.review_sha256,
    )
    def stable_result() -> None:
        stable()
        if (
            type(result) is not _RESULT
            or any(a is not b for a, b in zip((
                result.scope_sha256, result.revocation_witness_id,
                result.revocation_count, result.vetoed,
                result.attention_disposition, result.attention_review_sha256,
                result.review_sha256,
            ), result_epoch, strict=True))
        ):
            raise AttentionRevocationRejected("attention/veto report gained authority")

    for denial in _DENIALS:
        stable_result()
        if getattr(result, denial) is not False:
            raise AttentionRevocationRejected("attention/veto report gained authority")
        # Even the LAST denied-authority getter may reflectively rewrite its
        # own report. Revalidate result fields after every callback, not just
        # the original inputs / revocation ledger.
        stable_result()
    stable_result()
    return result
