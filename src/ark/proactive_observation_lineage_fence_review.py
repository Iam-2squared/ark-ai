"""Read-only observation lineage to prepared proactive Trigger binding.

Supplied observation metadata, hashes, clocks and policy are not authenticated.
This reviewer performs no capture, disclosure, notification or Tool execution;
even matching local lineage and persistent triggers confer no such authority.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

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
    initial = (
        envelopes, tuple(_epoch(x) for x in envelopes),
        selected_id, selected.observation_id,
        ledger.path, receipt.trigger_id, receipt.prepared_at_ms,
        policy.identity(),
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

    first_lineage = lineage()
    first_trigger = freshness()
    final_lineage = lineage()
    final_trigger = freshness()
    if (
        first_lineage != final_lineage
        or first_trigger != final_trigger
        or (
            envelopes, tuple(_epoch(x) for x in envelopes),
            selected_id, selected.observation_id,
            ledger.path, receipt.trigger_id, receipt.prepared_at_ms,
            policy.identity(),
        ) != initial
        or first_lineage.checked_at_ms != first_trigger.checked_at_ms
    ):
        raise SyntheticObservationTriggerRejected(
            "observation or trigger changed during disconnected review"
        )
    return SyntheticObservationTriggerReview(
        selected_id, first_lineage.lineage_digest,
        first_trigger.trigger_id, first_trigger.history.digest, now_ms,
    )
