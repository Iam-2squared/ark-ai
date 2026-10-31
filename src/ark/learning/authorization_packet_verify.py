"""Detached read-only check binding an unapproved V3 review packet to its input.

No storage, model access, GPU action, billing permission, human approval,
Candidate generation, protected evaluation or main merge is performed here.
The retained SHA-256 must originate independently from the packet itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .authorization import build_preflight_authorization_packet
from .execution import canonical_json, sha256_bytes
from .preflight import _assert_json_tree_epoch, _pin_json_tree

_SHA = re.compile(r"[0-9a-f]{64}\Z")


class LocalPacketBindingRejected(ValueError):
    """A review-only packet changed or disagreed with its retained input."""


@dataclass(frozen=True, slots=True)
class LocalPacketBindingWitness:
    snapshot_sha256: str
    packet_file_sha256: str
    internal_packet_sha256: str

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


_WITNESS_TYPE = LocalPacketBindingWitness
_DENIAL_FLAGS = (
    "external_compute_authorized",
    "candidate_generation_authorized",
    "protected_evaluation_authorized",
    "main_merge_authorized",
)


def verify_detached_authorization_packet(
    snapshot: dict,
    packet: dict,
    *,
    retained_packet_file_sha256: str,
) -> LocalPacketBindingWitness:
    """Rebuild the packet and compare canonical bytes with an external pin.

    This only detects drift of in-memory review evidence. A matching hash is
    neither independently authenticated provenance nor authorization.
    """
    if (
        type(snapshot) is not dict
        or type(packet) is not dict
        or type(retained_packet_file_sha256) is not str
        or _SHA.fullmatch(retained_packet_file_sha256) is None
    ):
        raise LocalPacketBindingRejected("exact review inputs and retained digest required")
    try:
        snapshot_epoch = _pin_json_tree(snapshot)
        packet_epoch = _pin_json_tree(packet)

        def unchanged() -> None:
            _assert_json_tree_epoch(snapshot, snapshot_epoch)
            _assert_json_tree_epoch(packet, packet_epoch)

        unchanged()
        expected = build_preflight_authorization_packet(snapshot)
        unchanged()
        actual_bytes = canonical_json(packet)
        unchanged()
        expected_bytes = canonical_json(expected)
        unchanged()
        if actual_bytes != expected_bytes:
            raise LocalPacketBindingRejected("packet disagrees with frozen input")
        observed = sha256_bytes(actual_bytes)
        unchanged()
        if observed != retained_packet_file_sha256:
            raise LocalPacketBindingRejected("independently retained packet bytes mismatch")
        # The packet's internal digest covers the payload WITHOUT that field,
        # while the separately retained file digest covers the complete bytes.
        core = dict(packet)
        internal = core.pop("packet_sha256")
        if (
            type(internal) is not str
            or _SHA.fullmatch(internal) is None
            or internal != sha256_bytes(canonical_json(core))
        ):
            raise LocalPacketBindingRejected("internal packet digest disagrees")
        unchanged()
        witness = LocalPacketBindingWitness(
            packet["execution_snapshot_sha256"], observed, internal,
        )
        unchanged()
        if (
            type(witness) is not _WITNESS_TYPE
            or type(witness.snapshot_sha256) is not str
            or witness.snapshot_sha256 != expected["execution_snapshot_sha256"]
            or witness.packet_file_sha256 is not observed
            or witness.internal_packet_sha256 is not internal
            or any(getattr(witness, flag) is not False for flag in _DENIAL_FLAGS)
        ):
            raise LocalPacketBindingRejected("packet witness gained authority")
        unchanged()
        if (
            type(witness) is not _WITNESS_TYPE
            or witness.snapshot_sha256 != expected["execution_snapshot_sha256"]
            or witness.packet_file_sha256 is not observed
            or witness.internal_packet_sha256 is not internal
        ):
            raise LocalPacketBindingRejected("packet witness changed after review")
        # Field reads can also be reflected callbacks. A witness getter that
        # returns the correct digest must not rewrite a packet or snapshot
        # after the preceding unchanged() check.
        unchanged()
        return witness
    except (TypeError, KeyError, OverflowError, UnicodeError, RecursionError) as exc:
        raise LocalPacketBindingRejected("unreadable detached review packet") from exc
