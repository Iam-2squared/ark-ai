"""Read-only observation lineage to prepared proactive Trigger binding.

Supplied observation metadata, hashes, clocks and policy are not authenticated.
This reviewer performs no capture, disclosure, notification or Tool execution;
even matching local lineage and persistent triggers confer no such authority.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from .observation_lineage_review import review_synthetic_observation_lineage
from .observations import ObservationEnvelope
from .proactive_synthetic_continuity_review import SyntheticTriggerWitness
from .proactive_synthetic_freshness_review import review_prepared_trigger_freshness
from .proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerReceipt,
    _hash,
)


class SyntheticObservationTriggerRejected(RuntimeError):
    """The local observation/trigger correlation cannot be trusted."""


@dataclass(frozen=True, slots=True)
class SyntheticObservationTriggerReview:
    observation_id: str
    lineage_digest: str
    trigger_id: str
    trigger_history_digest: str
    checked_at_ms: int

    @property
    def capture_authorized(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


def synthetic_observation_source_digest(source_id: str) -> str:
    """Untrusted, domain-separated local source identifier; no origin proof."""
    if type(source_id) is not str or not source_id.strip():
        raise SyntheticObservationTriggerRejected("exact synthetic observation source required")
    return _hash("ARK-untrusted-observation-source-v1", source_id)


def _epoch(envelope: ObservationEnvelope) -> tuple[object, ...]:
    return tuple(getattr(envelope, field.name) for field in fields(ObservationEnvelope))


def review_synthetic_observation_trigger(
    envelopes: tuple[ObservationEnvelope, ...],
    selected_id: str,
    *,
    privacy_scope: str,
    ledger: SyntheticProactiveLedger,
    receipt: SyntheticTriggerReceipt,
    policy: SyntheticTriggerPolicy,
    now_ms: int,
    max_age_ms: int,
    retained: SyntheticTriggerWitness | None = None,
) -> SyntheticObservationTriggerReview:
    """Revalidate one selected observation's source/content against a Trigger.

    Parent lineage is checked across the entire provided bounded window.
    Repeating both independent reviews rejects observed input/historical
    drift, not post-check edits, forged media or unauthenticated consent.
    """
    if (
        type(envelopes) is not tuple
        or type(selected_id) is not str or not selected_id
        or type(ledger) is not SyntheticProactiveLedger
        or type(receipt) is not SyntheticTriggerReceipt
        or type(policy) is not SyntheticTriggerPolicy
    ):
        raise SyntheticObservationTriggerRejected("exact observation/trigger inputs required")
    matching = tuple(
        value for value in envelopes
        if type(value) is ObservationEnvelope and value.observation_id == selected_id
    )
    if len(matching) != 1:
        raise SyntheticObservationTriggerRejected("selected observation must be unique")
    selected = matching[0]
    source_epoch = ledger.path
    if not isinstance(source_epoch, Path):
        raise SyntheticObservationTriggerRejected("observation trigger source is invalid")
    initial = (
        envelopes, tuple(_epoch(x) for x in envelopes),
        selected_id, selected.observation_id,
        receipt.trigger_id, receipt.prepared_at_ms,
        policy.identity(),
    )
    retained_epoch = None
    retained_rows_carrier = None
    if retained is not None:
        if type(retained) is not SyntheticTriggerWitness:
            raise SyntheticObservationTriggerRejected("exact retained trigger witness required")
        # The first integrity callback is already reentrant. Bind the caller's
        # original historical evidence before invoking it, including tuple
        # identity so an equal-valued clone cannot rebase the baseline.
        retained_rows_carrier = retained.row_hashes
        retained_epoch = (retained_rows_carrier, retained.digest)
        retained.assert_integrity()
        if (
            retained.row_hashes is not retained_rows_carrier
            or (retained.row_hashes, retained.digest) != retained_epoch
        ):
            raise SyntheticObservationTriggerRejected(
                "observation, policy or retained witness changed during review"
            )
    source_digest = synthetic_observation_source_digest(selected.source_id)
    observation_digest = selected.content_sha256

    def lineage():
        return review_synthetic_observation_lineage(
            envelopes, privacy_scope=privacy_scope,
            now_ms=now_ms, max_age_ms=max_age_ms,
        )

    def freshness():
        return review_prepared_trigger_freshness(
            ledger, receipt, policy,
            source_digest=source_digest, observation_digest=observation_digest,
            now_ms=now_ms, max_observation_age_ms=max_age_ms,
            retained=retained,
        )

    # Freshness independently pins its path only for the duration of one
    # read. An equal-value Path replacement BETWEEN those reads otherwise
    # looks identical to the outer evidence comparison.
    def ensure_source_epoch() -> None:
        if ledger.path is not source_epoch:
            raise SyntheticObservationTriggerRejected(
                "observation trigger source changed during review"
            )

    def ensure_input_epoch() -> None:
        ensure_source_epoch()
        if (
            (
                envelopes, tuple(_epoch(x) for x in envelopes),
                selected_id, selected.observation_id,
                receipt.trigger_id, receipt.prepared_at_ms,
                policy.identity(),
            ) != initial
            or retained is not None
            and (
                retained.row_hashes is not retained_rows_carrier
                or (retained.row_hashes, retained.digest) != retained_epoch
            )
        ):
            raise SyntheticObservationTriggerRejected(
                "observation, policy or retained witness changed during review"
            )
        ensure_source_epoch()

    # Source-digest hashing and policy identity construction are also
    # reentrant boundaries; reject changes before the first lineage reviewer.
    ensure_input_epoch()
    first_lineage = lineage()
    ensure_input_epoch()
    first_trigger = freshness()
    ensure_input_epoch()
    final_lineage = lineage()
    ensure_input_epoch()
    final_trigger = freshness()
    ensure_input_epoch()
    if (
        first_lineage != final_lineage
        or first_trigger != final_trigger
        or first_lineage.checked_at_ms != first_trigger.checked_at_ms
    ):
        raise SyntheticObservationTriggerRejected(
            "observation or trigger changed during disconnected review"
        )
    ensure_input_epoch()
    return SyntheticObservationTriggerReview(
        selected_id, first_lineage.lineage_digest,
        first_trigger.trigger_id, first_trigger.history.digest, now_ms,
    )
