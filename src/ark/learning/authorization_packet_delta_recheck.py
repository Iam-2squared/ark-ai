"""Detached recheck of an unapproved, field-path-only V3 packet delta.

This compares independently retained review output to two fresh local packet
file validations. It cannot authenticate reviewer actions or authorize training,
payment, Candidate output, protected V2 evaluation, promotion, or main merge.
"""

from __future__ import annotations

import re

from .authorization_packet_delta_review import (
    ReviewPacketDelta,
    ReviewPacketDeltaRejected,
    review_unapproved_packet_delta,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DENIALS = (
    "external_compute_authorized", "candidate_generation_authorized",
    "protected_evaluation_authorized", "main_merge_authorized",
)
_MAX_CHANGED_PATHS = 512
_MAX_PATH_CHARS = 512


class DetachedPacketDeltaRejected(ValueError):
    """The retained V3 delta receipt no longer matches the local packets."""


def _fields(receipt: ReviewPacketDelta) -> tuple[object, ...]:
    if type(receipt) is not ReviewPacketDelta:
        raise DetachedPacketDeltaRejected("exact detached packet delta required")
    fields = (
        receipt.old_file_sha256, receipt.new_file_sha256,
        receipt.changed_paths, receipt.delta_sha256,
    )
    previous_sha, next_sha, paths, digest = fields
    if (
        any(type(value) is not str or _SHA.fullmatch(value) is None
            for value in (previous_sha, next_sha, digest))
        or type(paths) is not tuple
        or len(paths) > _MAX_CHANGED_PATHS
        or any(
            type(path) is not str
            or not path or len(path) > _MAX_PATH_CHARS
            or any(ord(ch) < 33 or ord(ch) > 126 for ch in path)
            for path in paths
        )
        or tuple(sorted(set(paths))) != paths
    ):
        raise DetachedPacketDeltaRejected("noncanonical detached packet delta")
    return fields


def verify_detached_unapproved_packet_delta(
    retained: ReviewPacketDelta,
    old_snapshot: dict,
    new_snapshot: dict,
    old_path: object,
    new_path: object,
    *,
    retained_old_file_sha256: str,
    retained_new_file_sha256: str,
) -> None:
    """Recompute a field-name-only review and reject stale detached receipts.

    Local file/hash comparison does not grant historical custody or attest
    anything about an execution identity, human decision or billing permission.
    """
    pinned = _fields(retained)
    if (
        type(retained_old_file_sha256) is not str
        or type(retained_new_file_sha256) is not str
        or pinned[0] != retained_old_file_sha256
        or pinned[1] != retained_new_file_sha256
    ):
        raise DetachedPacketDeltaRejected("retained packet SHA mismatch")
    descriptors = tuple(getattr(ReviewPacketDelta, name) for name in _DENIALS)

    def stable() -> None:
        if (
            any(
                now is not old
                for now, old in zip(_fields(retained), pinned, strict=True)
            )
            or any(
                getattr(ReviewPacketDelta, name) is not desc
                for name, desc in zip(_DENIALS, descriptors, strict=True)
            )
        ):
            raise DetachedPacketDeltaRejected(
                "retained packet delta changed during recheck"
            )

    stable()
    for flag in _DENIALS:
        if getattr(retained, flag) is not False:
            raise DetachedPacketDeltaRejected("retained delta gained authority")
        stable()

    try:
        expected = review_unapproved_packet_delta(
            old_snapshot, new_snapshot, old_path, new_path,
            retained_old_file_sha256=retained_old_file_sha256,
            retained_new_file_sha256=retained_new_file_sha256,
        )
    except ReviewPacketDeltaRejected as exc:
        raise DetachedPacketDeltaRejected("local packet files cannot be rechecked") from exc
    stable()
    expected_fields = _fields(expected)
    if expected_fields != pinned:
        raise DetachedPacketDeltaRejected("retained packet delta no longer matches")

    def stable_expected() -> None:
        # The fresh reviewer is a callback. Its result is an exact-class
        # passive receipt, but even equal-valued replacement of its original
        # field carriers must not pass an authority-denial callback.
        if any(
            now is not prior
            for now, prior in zip(_fields(expected), expected_fields, strict=True)
        ):
            raise DetachedPacketDeltaRejected(
                "fresh packet delta changed during denial"
            )
        stable()

    stable_expected()
    for flag in _DENIALS:
        if getattr(expected, flag) is not False:
            raise DetachedPacketDeltaRejected("fresh packet delta gained authority")
        stable_expected()
        # Do not allow a fresh callback to invalidate the previously denied
        # retained receipt without ever rechecking its flags.
        if any(getattr(retained, name) is not False for name in _DENIALS):
            raise DetachedPacketDeltaRejected("retained delta gained authority")
        stable_expected()
    stable_expected()
    return None
