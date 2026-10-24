"""Disconnected observation parent-lineage guard over metadata-only fixtures.

A content hash is not a signature, provenance proof or verified media source.
No hardware capture, processing of raw media, notification or ToolBackend
operation is permitted by this isolated reviewer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .observation_window_review import ObservationWindowReview
from .observations import ObservationEnvelope


class SyntheticObservationLineageRejected(RuntimeError):
    """The fixture's claimed parent-chain identity is inconsistent."""


@dataclass(frozen=True, slots=True)
class SyntheticObservationLineageWitness:
    privacy_scope: str
    checked_at_ms: int
    observation_count: int
    lineage_digest: str

    @property
    def media_capture_authorized(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False


def review_synthetic_observation_lineage(
    envelopes: tuple[ObservationEnvelope, ...],
    *,
    privacy_scope: str,
    now_ms: int,
    max_age_ms: int,
) -> SyntheticObservationLineageWitness:
    """Validate resolved parent hashes, privacy and per-source chronology.

    Every parent must occur exactly once in the supplied local window.
    Matching hashes alone are never trusted if the parent is ambiguous.
    The result is an inert, content-free deterministic review witness.
    """
    if type(envelopes) is not tuple:
        raise SyntheticObservationLineageRejected("exact observation tuple required")
    # Existing window construction enforces bounded membership, same privacy
    # scope, canonical envelope identity, age and caller-clock constraints.
    window = ObservationWindowReview(
        privacy_scope, now_ms, max_age_ms, envelopes,
    )
    window.assert_fresh_at(now_ms)
    by_content: dict[str, list[ObservationEnvelope]] = {}
    for envelope in envelopes:
        by_content.setdefault(envelope.content_sha256, []).append(envelope)

    parents: dict[str, str | None] = {}
    for envelope in envelopes:
        parent_id = None
        if envelope.parent_sha256 is not None:
            options = by_content.get(envelope.parent_sha256, [])
            if not options:
                raise SyntheticObservationLineageRejected(
                    "observation parent hash is unresolved"
                )
            if len(options) != 1:
                raise SyntheticObservationLineageRejected(
                    "observation parent digest is ambiguous"
                )
            parent = options[0]
            if parent.source_id != envelope.source_id:
                raise SyntheticObservationLineageRejected(
                    "observation parent crosses source boundary"
                )
            if parent.ingested_at_ms > envelope.ingested_at_ms:
                raise SyntheticObservationLineageRejected(
                    "observation parent timestamp is after child"
                )
            parent_id = parent.observation_id
        parents[envelope.observation_id] = parent_id

    completed: set[str] = set()
    for start in parents:
        current: str | None = start
        seen: set[str] = set()
        while current is not None and current not in completed:
            if current in seen:
                raise SyntheticObservationLineageRejected(
                    "observation parent-chain cycle detected"
                )
            seen.add(current)
            current = parents[current]
        completed.update(seen)

    edges = tuple(sorted(parents.items()))
    payload = json.dumps(
        (1, privacy_scope, now_ms, max_age_ms, edges),
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = "olineage_" + hashlib.sha256(
        b"ARK-observation-lineage-v1\0" + payload
    ).hexdigest()
    # The cached window detects reflected changes to envelope metadata while
    # walking the graph. This does not attest source authenticity.
    window.assert_fresh_at(now_ms)
    return SyntheticObservationLineageWitness(
        privacy_scope, now_ms, len(envelopes), digest,
    )
