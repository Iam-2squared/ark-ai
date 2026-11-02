"""Read-only comparison of two independently retained V3 review packets.

The resulting change set contains ONLY JSON field paths, never values. A
packet delta does not authenticate a reviewer, approve payment, start a model,
open V2, authorize Candidate generation, or grant a main merge.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

from .authorization import build_preflight_authorization_packet
from .authorization_packet_file_review import verify_local_authorization_packet_file
from .execution import ExecutionBlocked, canonical_json
from .preflight import _assert_json_tree_epoch, _pin_json_tree

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-v3-unapproved-packet-delta-review-v1\0"
_DENIALS = (
    "external_compute_authorized", "candidate_generation_authorized",
    "protected_evaluation_authorized", "main_merge_authorized",
)


class ReviewPacketDeltaRejected(ValueError):
    """An unapproved V3 packet change set could not be verified."""


@dataclass(frozen=True, slots=True)
class ReviewPacketDelta:
    old_file_sha256: str
    new_file_sha256: str
    changed_paths: tuple[str, ...]
    delta_sha256: str

    @property
    def external_compute_authorized(self) -> bool:
        return False

    @property
    def candidate_generation_authorized(self) -> bool:
        return False

    @property
    def protected_evaluation_authorized(self) -> bool:
        return False

    @property
    def main_merge_authorized(self) -> bool:
        return False


def _leaf_bytes(value: dict) -> dict[str, bytes]:
    """Bounded type-aware leaves with unambiguous, value-free field paths.

    Literal key delimiters are escaped before joining, so a key named
    "a.b" cannot impersonate the nested path a.b. Empty containers are
    leaves too; changing {} into [] must not disappear from the delta.
    Ordinary alphanumeric dotted paths retain their existing spelling.
    """
    leaves: dict[str, bytes] = {}

    def escaped(key: str) -> str:
        # Preserve empty keys; reserved "~" always escapes before a marker.
        # Render controls, bidi/format and combining marks (which can\n        # visually overlay prior characters) as unambiguous components.
        if key == "":
            return "~5"
        delimiters = {"~": "~0", ".": "~2", "[": "~3", "]": "~4", "\\": "~6"}
        pieces = []
        for char in key:
            if (char != " " and not char.isprintable()) or (\n                unicodedata.category(char).startswith("M")\n            ):
                pieces.append(f"~u{{{ord(char):X}}}")
            else:
                pieces.append(delimiters.get(char, char))
        return "".join(pieces)

    def add(path: str, node: object) -> None:
        if path in leaves or len(path) > 512 or len(leaves) >= 512:
            raise ReviewPacketDeltaRejected("ambiguous or oversized review field path")
        leaves[path] = canonical_json(node)

    def descend(node: object, path: str, depth: int) -> None:
        if depth > 16 or len(leaves) > 512 or len(path) > 512:
            raise ReviewPacketDeltaRejected("review change-set budget exceeded")
        if type(node) is dict:
            if len(node) > 128 or any(type(key) is not str for key in node):
                raise ReviewPacketDeltaRejected("review contains invalid field keys")
            if not node:
                add(path, node)
            for key in sorted(node):
                segment = escaped(key)
                descend(
                    node[key], path + "." + segment if path else segment,
                    depth + 1,
                )
        elif type(node) is list:
            if len(node) > 128:
                raise ReviewPacketDeltaRejected("review array budget exceeded")
            if not node:
                add(path, node)
            for index, item in enumerate(node):
                descend(item, path + "[" + str(index) + "]", depth + 1)
        else:
            # Canonical bytes are type-aware: True and 1 must not compare
            # equal just because Python's bool subclasses int.
            add(path, node)

    descend(value, "", 0)
    return leaves


def review_unapproved_packet_delta(
    old_snapshot: dict,
    new_snapshot: dict,
    old_path: object,
    new_path: object,
    *,
    retained_old_file_sha256: str,
    retained_new_file_sha256: str,
) -> ReviewPacketDelta:
    """Verify both saved unapproved packets before reporting changed field paths.

    Comparison is independent of model/GPU I/O and never opens an execution
    gate. Both file digests are caller-supplied independent custody inputs.
    """
    if (
        type(old_snapshot) is not dict
        or type(new_snapshot) is not dict
        or type(retained_old_file_sha256) is not str
        or _SHA.fullmatch(retained_old_file_sha256) is None
        or type(retained_new_file_sha256) is not str
        or _SHA.fullmatch(retained_new_file_sha256) is None
    ):
        raise ReviewPacketDeltaRejected("exact unapproved review inputs required")
    try:
        old_epoch = _pin_json_tree(old_snapshot)
        new_epoch = _pin_json_tree(new_snapshot)

        def stable() -> None:
            _assert_json_tree_epoch(old_snapshot, old_epoch)
            _assert_json_tree_epoch(new_snapshot, new_epoch)

        stable()
        # The local file verifier independently rebuilds each packet,
        # checks its unapproved snapshot and reopens exact file bytes.
        verify_local_authorization_packet_file(
            old_snapshot, old_path,
            retained_packet_file_sha256=retained_old_file_sha256,
        )
        stable()
        verify_local_authorization_packet_file(
            new_snapshot, new_path,
            retained_packet_file_sha256=retained_new_file_sha256,
        )
        stable()
        # Rebuild after validating files; never trust packet dictionaries
        # supplied by a different source or compare only their internal SHA.
        first = build_preflight_authorization_packet(old_snapshot)
        stable()
        second = build_preflight_authorization_packet(new_snapshot)
        stable()
        previous = _leaf_bytes(first)
        upcoming = _leaf_bytes(second)
        stable()
        changed = tuple(sorted(
            key for key in previous.keys() | upcoming.keys()
            if previous.get(key) != upcoming.get(key)
        ))
        if len(changed) > 512:
            raise ReviewPacketDeltaRejected("review change-set budget exceeded")
        digest = hashlib.sha256(
            _DOMAIN + canonical_json((
                retained_old_file_sha256, retained_new_file_sha256, changed,
            ))
        ).hexdigest()
        stable()
        # No successful earlier read is evidence about a different later
        # file epoch. Reopen both sources AFTER comparison callbacks.
        verify_local_authorization_packet_file(
            old_snapshot, old_path,
            retained_packet_file_sha256=retained_old_file_sha256,
        )
        stable()
        verify_local_authorization_packet_file(
            new_snapshot, new_path,
            retained_packet_file_sha256=retained_new_file_sha256,
        )
        stable()
        result = ReviewPacketDelta(
            retained_old_file_sha256, retained_new_file_sha256, changed, digest,
        )
        pinned = (
            result.old_file_sha256, result.new_file_sha256,
            result.changed_paths, result.delta_sha256,
        )
        descriptors = tuple(getattr(ReviewPacketDelta, flag) for flag in _DENIALS)

        def stable_result() -> None:
            if (
                type(result) is not ReviewPacketDelta
                or any(
                    now is not original for now, original in zip(
                        (result.old_file_sha256, result.new_file_sha256,
                         result.changed_paths, result.delta_sha256),
                        pinned, strict=True,
                    )
                )
                or any(
                    getattr(ReviewPacketDelta, name) is not descriptor
                    for name, descriptor in zip(_DENIALS, descriptors, strict=True)
                )
            ):
                raise ReviewPacketDeltaRejected("review delta changed after comparison")

        stable_result()
        for name in _DENIALS:
            if getattr(result, name) is not False:
                raise ReviewPacketDeltaRejected("review delta gained authority")
            stable_result()
            stable()
        # A denial getter may alter the packet files, so recheck both before
        # returning, without claiming filesystem race immunity.
        verify_local_authorization_packet_file(
            old_snapshot, old_path,
            retained_packet_file_sha256=retained_old_file_sha256,
        )
        stable_result()
        stable()
        verify_local_authorization_packet_file(
            new_snapshot, new_path,
            retained_packet_file_sha256=retained_new_file_sha256,
        )
        stable_result()
        stable()
        return result
    except (
        ExecutionBlocked, ValueError, TypeError, KeyError,
        RecursionError, OverflowError,
    ) as exc:
        raise ReviewPacketDeltaRejected("unapproved packet delta review denied") from exc
