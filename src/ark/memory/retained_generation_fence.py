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
_REVIEW_TYPE = MemoryGenerationReview
_ORIGINAL_DENIALS = tuple(vars(_REVIEW_TYPE)[name] for name in _DENIALS)
_FIELDS = (
    "memory_id", "event_count", "generation_count", "live_revision",
    "expected_revision", "revision_reuse_possible", "retained_history_sha256",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_FIELDS = tuple(vars(_REVIEW_TYPE)[name] for name in _FIELDS)
_ORIGINAL_HOOKS = tuple(vars(_REVIEW_TYPE).get(name) for name in _HOOKS)
_ORIGINAL_REVIEW = review_memory_revision_reuse


class RetainedMemoryGenerationRejected(MemorySchemaError):
    """The retained observation does not match the current local generation."""


def _assert_original_denials() -> None:
    # Before reading retained fields or passing a private store to a callback,
    # reject substituted record descriptors and the imported review function.
    if (
        MemoryGenerationReview is not _REVIEW_TYPE
        or review_memory_revision_reuse is not _ORIGINAL_REVIEW
        or any(
            vars(_REVIEW_TYPE).get(name) is not original
            for names, originals in (
                (_DENIALS, _ORIGINAL_DENIALS),
                (_FIELDS, _ORIGINAL_FIELDS),
                (_HOOKS, _ORIGINAL_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise RetainedMemoryGenerationRejected(
            "retained generation authority descriptor changed"
        )


def _fields(review: MemoryGenerationReview) -> tuple[object, ...]:
    if type(review) is not _REVIEW_TYPE:
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
        # Every historical lifetime needs a create; every earlier lifetime
        # needs a terminal event. A live revision R needs R-1 updates in
        # its current lifetime. Reject geometrically impossible retained
        # observations BEFORE reviewing private SQLite history.
        or (generations == 0 and (events != 0 or live is not None))
        or (generations > 0 and events < (
            2 * generations - 1
            + (live - 1 if live is not None else 1)
        ))
        or type(digest) is not str or _SHA.fullmatch(digest) is None
    ):
        raise RetainedMemoryGenerationRejected("invalid retained generation fields")
    return fields


# Comparisons are deny-only.  Do not pass retained private identifiers or a
# SQLite handle through a replacement parser/review function.  Import-time
# binding checks cannot authenticate an independent witness or a real writer.
_ORIGINAL_SHA_PARSER = _SHA
_ORIGINAL_ID_PARSER = _ID
_ORIGINAL_EVENT_BUDGET = _MAX_EVENTS
_ORIGINAL_SQLITE_LIMIT = SQLITE_INT_MAX
_ORIGINAL_FIELDS_READER = _fields
_ORIGINAL_DENIAL_CHECK = _assert_original_denials
# Keep a second, independent import-time baseline for the protocol's own
# lookup tables and captured class descriptors. Rebinding the lists that
# select which False-only properties to inspect must not suppress a denial.
_ORIGINAL_DENIAL_NAMES = _DENIALS
_ORIGINAL_FIELD_NAMES = _FIELDS
_ORIGINAL_HOOK_NAMES = _HOOKS
_ORIGINAL_REVIEW_TYPE = _REVIEW_TYPE
_ORIGINAL_DENIAL_DESCRIPTORS = _ORIGINAL_DENIALS
_ORIGINAL_FIELD_DESCRIPTORS = _ORIGINAL_FIELDS
_ORIGINAL_HOOK_DESCRIPTORS = _ORIGINAL_HOOKS
_ORIGINAL_REVIEW_CALLBACK = _ORIGINAL_REVIEW


def _assert_retained_generation_protocol() -> None:
    if (
        _SHA is not _ORIGINAL_SHA_PARSER
        or _ID is not _ORIGINAL_ID_PARSER
        # Value equality accepts e.g. 40000.0 or a hostile __eq__ carrier.
        # Both limits must remain the ORIGINAL exact integer objects before
        # any retained identifiers or private SQLite inputs are inspected.
        or type(_MAX_EVENTS) is not int
        or type(_ORIGINAL_EVENT_BUDGET) is not int
        or _MAX_EVENTS is not _ORIGINAL_EVENT_BUDGET
        or type(SQLITE_INT_MAX) is not int
        or type(_ORIGINAL_SQLITE_LIMIT) is not int
        or SQLITE_INT_MAX is not _ORIGINAL_SQLITE_LIMIT
        or _fields is not _ORIGINAL_FIELDS_READER
        or _assert_original_denials is not _ORIGINAL_DENIAL_CHECK
        or _DENIALS is not _ORIGINAL_DENIAL_NAMES
        or _FIELDS is not _ORIGINAL_FIELD_NAMES
        or _HOOKS is not _ORIGINAL_HOOK_NAMES
        or _REVIEW_TYPE is not _ORIGINAL_REVIEW_TYPE
        or _ORIGINAL_DENIALS is not _ORIGINAL_DENIAL_DESCRIPTORS
        or _ORIGINAL_FIELDS is not _ORIGINAL_FIELD_DESCRIPTORS
        or _ORIGINAL_HOOKS is not _ORIGINAL_HOOK_DESCRIPTORS
        or _ORIGINAL_REVIEW is not _ORIGINAL_REVIEW_CALLBACK
    ):
        raise RetainedMemoryGenerationRejected(
            "retained generation parser or review helper changed"
        )


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
    _assert_retained_generation_protocol()
    _assert_original_denials()
    pinned = _fields(retained)
    if (
        type(expected_revision) is not int
        or not 0 <= expected_revision <= SQLITE_INT_MAX
        or pinned[4] != expected_revision
    ):
        raise RetainedMemoryGenerationRejected("retained CAS revision mismatch")

    def stable() -> None:
        _assert_retained_generation_protocol()
        _assert_original_denials()
        latest = _fields(retained)
        if (
            any(now is not original for now, original in zip(
                latest, pinned, strict=True,
            ))
        ):
            raise RetainedMemoryGenerationRejected(
                "retained generation changed during verification"
            )

    stable()
    for flag in _DENIALS:
        _assert_original_denials()
        if getattr(retained, flag) is not False:
            raise RetainedMemoryGenerationRejected(
                "retained generation gained authority"
            )
        stable()

    _assert_retained_generation_protocol()
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
        _assert_original_denials()
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
    _assert_retained_generation_protocol()
    return None
