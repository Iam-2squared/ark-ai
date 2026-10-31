"""Bounded, read-only continuity review over independently retained Memory epochs.

This consumes exact local Memory review objects, not an authenticated log.
Even a chain that passes cannot prove that appended historical prefixes were
preserved or that a trusted writer produced them. No disclosure or execution.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .atomic_epoch_review import AtomicMemoryEpochReview
from .contracts import MemorySchemaError
from .retained_epoch_review import (
    RetainedMemoryEpochComparison,
    review_retained_memory_epoch,
)
from .retained_epoch_review import (
    _validate as _validate_epoch,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-memory-retained-epoch-chain-v1\0"
_MAX_EPOCHS = 16
_EPOCH_TYPE = AtomicMemoryEpochReview
_EDGE_TYPE = RetainedMemoryEpochComparison


@dataclass(frozen=True, slots=True)
class RetainedMemoryChainReview:
    observations: int
    scope_fingerprints: tuple[str, ...]
    added_event_counts: tuple[int, ...]
    status: str
    chain_digest: str

    @property
    def historical_prefix_proven(self) -> bool:
        return False

    @property
    def independent_writer_proven(self) -> bool:
        return False

    @property
    def custody_authenticated(self) -> bool:
        return False

    @property
    def memory_disclosure_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False


_RESULT_TYPE = RetainedMemoryChainReview


def review_retained_memory_chain(
    epochs: tuple[AtomicMemoryEpochReview, ...],
) -> RetainedMemoryChainReview:
    """Compare an ordered local observation sequence without trusting appends.

    Every pair must satisfy the two-epoch CAS/history comparison. Count growth
    is reported as unverified even when all individual SQLite views are valid.
    Retained objects must come from distinct observations and stay unchanged
    throughout all comparison callbacks.
    """
    if (
        type(epochs) is not tuple
        or not 2 <= len(epochs) <= _MAX_EPOCHS
        or any(type(epoch) is not _EPOCH_TYPE for epoch in epochs)
        or len({id(epoch) for epoch in epochs}) != len(epochs)
    ):
        raise MemorySchemaError("exact independent Memory epoch chain required")
    originals = tuple(epochs)
    pinned = tuple(_validate_epoch(epoch) for epoch in originals)
    scope_ids = pinned[0][0]
    if any(fields[0] != scope_ids for fields in pinned):
        raise MemorySchemaError("Memory chain scope identity changed")

    def stable() -> None:
        if (
            type(epochs) is not tuple
            or len(epochs) != len(originals)
            or any(
                current is not original or type(current) is not _EPOCH_TYPE
                or any(now is not initial for now, initial in zip(
                    _validate_epoch(current), fields, strict=True,
                ))
                for current, original, fields in zip(
                    epochs, originals, pinned, strict=True,
                )
            )
        ):
            raise MemorySchemaError("Memory epoch chain carrier changed")

    stable()
    totals = [0] * len(scope_ids)
    edge_summaries: list[tuple[object, ...]] = []
    advanced = False
    pinned_edges: list[tuple[object, ...]] = []

    def stable_edges() -> None:
        for edge, scopes, counts, status, digest in pinned_edges:
            if (
                type(edge) is not _EDGE_TYPE
                or edge.scope_fingerprints is not scopes
                or edge.new_event_counts is not counts
                or edge.status is not status
                or edge.comparison_digest is not digest
                or edge.historical_prefix_proven is not False
                or edge.independent_writer_proven is not False
                or edge.custody_authenticated is not False
                or edge.memory_disclosure_authorized is not False
                or edge.dispatch_authorized is not False
            ):
                raise MemorySchemaError("Memory chain earlier edge result changed")

    for index, (previous, current) in enumerate(
        zip(originals, originals[1:], strict=False),
    ):
        stable()
        stable_edges()
        edge = review_retained_memory_epoch(previous, current)
        stable()
        stable_edges()
        prev_fields = pinned[index]
        next_fields = pinned[index + 1]
        growth = tuple(
            later - before for before, later in zip(
                prev_fields[2], next_fields[2], strict=True,
            )
        )
        expected_status = (
            "ADVANCED_HISTORY_UNVERIFIED"
            if any(growth) else "UNCHANGED_LOCAL_CONTENT"
        )
        if (
            type(edge) is not _EDGE_TYPE
            or edge.scope_fingerprints != scope_ids
            or type(edge.new_event_counts) is not tuple
            or edge.new_event_counts != growth
            or type(edge.status) is not str
            or edge.status != expected_status
            or type(edge.comparison_digest) is not str
            or _SHA.fullmatch(edge.comparison_digest) is None
            or edge.historical_prefix_proven is not False
            or edge.independent_writer_proven is not False
            or edge.custody_authenticated is not False
            or edge.memory_disclosure_authorized is not False
            or edge.dispatch_authorized is not False
        ):
            raise MemorySchemaError("Memory chain edge result changed")
        pinned_edges.append((
            edge, edge.scope_fingerprints, edge.new_event_counts,
            edge.status, edge.comparison_digest,
        ))
        stable_edges()
        advanced |= any(growth)
        for j, count in enumerate(growth):
            totals[j] += count
        edge_summaries.append(
            (prev_fields[5], next_fields[5], edge.comparison_digest,
             edge.status, growth),
        )
        stable()
        stable_edges()

    status = (
        "ADVANCED_HISTORY_UNVERIFIED"
        if advanced else "UNCHANGED_LOCAL_CONTENT"
    )
    counts = tuple(totals)
    # Bind every observation including unchanged intermediate clock epochs,
    # rather than hashing only endpoints (which would miss a fork/rejoin).
    payload = (
        tuple((fields[0], fields[1], fields[2], fields[3],
               fields[4], fields[5]) for fields in pinned),
        edge_summaries, status,
    )
    encoded = json.dumps(
        payload, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("ascii")
    stable()
    stable_edges()
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    stable_edges()
    result = RetainedMemoryChainReview(
        len(originals), scope_ids, counts, status, digest,
    )
    stable()
    stable_edges()
    if (
        type(result) is not _RESULT_TYPE
        or type(result.observations) is not int
        or result.observations != len(originals)
        or result.scope_fingerprints is not scope_ids
        or result.added_event_counts is not counts
        or result.status is not status
        or result.chain_digest is not digest
        or result.historical_prefix_proven is not False
        or result.independent_writer_proven is not False
        or result.custody_authenticated is not False
        or result.memory_disclosure_authorized is not False
        or result.dispatch_authorized is not False
    ):
        raise MemorySchemaError("Memory chain result changed")
    # Denied-authority getters can be reflected callbacks. Their final
    # False result must not conceal a late rewrite of an observed Memory
    # epoch or of this otherwise-valid synthetic review.
    stable()
    stable_edges()
    if (
        type(result) is not _RESULT_TYPE
        or type(result.observations) is not int
        or result.observations != len(originals)
        or result.scope_fingerprints is not scope_ids
        or result.added_event_counts is not counts
        or result.status is not status
        or result.chain_digest is not digest
    ):
        raise MemorySchemaError("Memory chain result changed after authority review")
    return result
