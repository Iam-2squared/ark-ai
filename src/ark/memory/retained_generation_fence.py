"""Detached, read-only Memory CAS generation continuity check.

The caller retains a previous generation review independently. The new check
rejects any changed observed local event history, including delete/recreate at
the same numeric revision (ABA). A successful comparison is NOT an atomic CAS
guard, a writer identity, provenance, consent, or permission to mutate Memory.
"""

from __future__ import annotations

import re

from .cas_generation_review import (
    MemoryGenerationReview,
    MemoryGenerationReviewRejected,
    review_memory_revision_reuse,
)
from .contracts import MemorySchemaError, MemoryScope
from .sqlite_store import SQLITE_INT_MAX, SQLiteMemoryStore

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"mem_[0-9a-f]{64}\Z")
_MAX_EVENTS = 40_000
_DENIALS = ("write_authorized", "erase_authorized", "generation_authenticated")


class RetainedMemoryGenerationRejected(MemorySchemaError):
    """The retained observation does not match the current local generation."""


def _fields(review: MemoryGenerationReview) -> tuple[object, ...]:
    if type(review) is not MemoryGenerationReview:
        raise RetainedMemoryGenerationRejected("exact retained generation review required")
    fields = (
        review.memory_id, review.event_count, review.generation_count,
        review.live_revision, review.expected_revision,
        review.revision_reuse_possible, review.retained_history_sha256,
    )
    memory_id, events, generations, live, expected, reuse, digest = fields
    if (
        type(memory_id) is not str or _ID.fullmatch(memory_id) is None
        or type(events) is not int or not 0 <= events <= _MAX_EVENTS
        or type(generations) is not int or not 0 <= generations <= events
        or (live is not None and (
            type(live) is not int or not 1 <= live <= SQLITE_INT_MAX
        ))
        or type(expected) is not int or not 0 <= expected <= SQLITE_INT_MAX
        or type(reuse) is not bool
        or reuse is not (generations > 1 and live == expected)
        or type(digest) is not str or _SHA.fullmatch(digest) is None
    ):
        raise RetainedMemoryGenerationRejected("invalid retained generation fields")
    return fields


def verify_retained_memory_generation(
    retained: MemoryGenerationReview,
    store: SQLiteMemoryStore,
    scope: MemoryScope,
    source_id: str,
    *,
    expected_revision: int,
) -> None:
    """Verify a separately held observation against a fresh SQLite snapshot.

    Return only None after an exact match. Do not perform or authorize a CAS
    write: an external writer can advance the database immediately afterward.
    A detached SHA cannot attest malicious replacement of BOTH observations.
    """
    pinned = _fields(retained)
    if (
        type(expected_revision) is not int
        or not 0 <= expected_revision <= SQLITE_INT_MAX
        or pinned[4] != expected_revision
    ):
        raise RetainedMemoryGenerationRejected("retained CAS revision mismatch")
    descriptors = tuple(
        getattr(MemoryGenerationReview, flag) for flag in _DENIALS
    )

    def stable() -> None:
        latest = _fields(retained)
        if (
            any(now is not original for now, original in zip(
                latest, pinned, strict=True,
            ))
            or any(
                getattr(MemoryGenerationReview, flag) is not descriptor
                for flag, descriptor in zip(_DENIALS, descriptors, strict=True)
            )
        ):
            raise RetainedMemoryGenerationRejected(
                "retained generation changed during verification"
            )

    stable()
    for flag in _DENIALS:
        if getattr(retained, flag) is not False:
            raise RetainedMemoryGenerationRejected(
                "retained generation gained authority"
            )
        stable()

    try:
        observed = review_memory_revision_reuse(
            store, scope, source_id, expected_revision=expected_revision,
        )
    except MemoryGenerationReviewRejected as exc:
        raise RetainedMemoryGenerationRejected(
            "current Memory generation cannot be reconciled"
        ) from exc
    stable()
    if _fields(observed) != pinned:
        raise RetainedMemoryGenerationRejected(
            "Memory generation changed since retained observation"
        )
    for flag in _DENIALS:
        if getattr(observed, flag) is not False:
            raise RetainedMemoryGenerationRejected(
                "current generation report gained authority"
            )
        stable()
        if _fields(observed) != pinned:
            raise RetainedMemoryGenerationRejected(
                "current generation report changed during denial"
            )
    stable()
    if _fields(observed) != pinned:
        raise RetainedMemoryGenerationRejected(
            "current generation changed after verification"
        )
    # Comparison is a short-lived local observation, not a lock or permission.
    return None
