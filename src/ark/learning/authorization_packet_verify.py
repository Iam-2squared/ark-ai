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
# The original denial method itself is part of the permission boundary:
# a different callback returning False is not an equivalent authority proof.
_ORIGINAL_DENIAL_DESCRIPTORS = tuple(
    getattr(_WITNESS_TYPE, name) for name in _DENIAL_FLAGS
)
_ORIGINAL_DENIAL_FLAGS_VECTOR = _DENIAL_FLAGS

# Absence is a first-class part of the class contract. In particular, an
# explicitly installed None must not compare equal to an inherited/missing
# lookup hook.
_WITNESS_CLASS_HOOK_NAMES = (
    "__new__", "__getattribute__", "__getattr__", "__setattr__", "__delattr__",
)
_WITNESS_CLASS_HOOK_ABSENT = object()
_ORIGINAL_WITNESS_INIT = vars(_WITNESS_TYPE)["__init__"]
_ORIGINAL_WITNESS_CLASS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name, _WITNESS_CLASS_HOOK_ABSENT)
    for name in _WITNESS_CLASS_HOOK_NAMES
)
_ORIGINAL_WITNESS_CLASS_HOOKS_VECTOR = _WITNESS_CLASS_HOOK_NAMES


def _require_original_witness_contract(
    *,
    _witness_type: type = _WITNESS_TYPE,
    _hook_names: tuple[str, ...] = _WITNESS_CLASS_HOOK_NAMES,
    _hook_absent: object = _WITNESS_CLASS_HOOK_ABSENT,
    _original_init: object = _ORIGINAL_WITNESS_INIT,
    _original_hooks: tuple[object, ...] = _ORIGINAL_WITNESS_CLASS_HOOKS,
    _denial_flags: tuple[str, ...] = _DENIAL_FLAGS,
    _original_denials: tuple[object, ...] = _ORIGINAL_DENIAL_DESCRIPTORS,
) -> None:
    """Pin witness construction and class hooks before any witness access."""
    namespace = vars(_witness_type)
    if (
        LocalPacketBindingWitness is not _witness_type
        or _WITNESS_TYPE is not _witness_type
        or namespace.get("__init__") is not _original_init
        or _ORIGINAL_WITNESS_INIT is not _original_init
        or _WITNESS_CLASS_HOOK_NAMES is not _hook_names
        or _ORIGINAL_WITNESS_CLASS_HOOKS_VECTOR is not _hook_names
        or _WITNESS_CLASS_HOOK_ABSENT is not _hook_absent
        or _ORIGINAL_WITNESS_CLASS_HOOKS is not _original_hooks
        or any(
            (name in namespace) != (original is not _hook_absent)
            or (name in namespace and namespace[name] is not original)
            for name, original in zip(_hook_names, _original_hooks, strict=True)
        )
    ):
        raise LocalPacketBindingRejected("packet witness class lookup contract changed")
    if (
        _DENIAL_FLAGS is not _denial_flags
        or _ORIGINAL_DENIAL_FLAGS_VECTOR is not _denial_flags
        or _ORIGINAL_DENIAL_DESCRIPTORS is not _original_denials
        or any(
            namespace.get(name) is not original
            for name, original in zip(
                _denial_flags, _original_denials, strict=True,
            )
        )
    ):
        raise LocalPacketBindingRejected(
            "packet witness gained authority: denial descriptor inventory changed"
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
    # Retain the guard in this invocation's local frame so a serializer or
    # caller-owned callback cannot replace the module binding mid-review.
    witness_guard = _require_original_witness_contract
    witness_guard()
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
            if _require_original_witness_contract is not witness_guard:
                raise LocalPacketBindingRejected(
                    "packet witness class lookup contract changed"
                )
            witness_guard()
            _assert_json_tree_epoch(snapshot, snapshot_epoch)
            _assert_json_tree_epoch(packet, packet_epoch)
            if _require_original_witness_contract is not witness_guard:
                raise LocalPacketBindingRejected(
                    "packet witness class lookup contract changed"
                )
            witness_guard()

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
        unchanged()
        witness = LocalPacketBindingWitness(
            packet["execution_snapshot_sha256"], observed, internal,
        )
        unchanged()

        def read_witness(name: str) -> object:
            # A field/denial descriptor is a callback boundary. Recheck the
            # class lookup policy immediately after each getter so a getter
            # cannot install a new __getattribute__ before the next read.
            if _require_original_witness_contract is not witness_guard:
                raise LocalPacketBindingRejected(
                    "packet witness class lookup contract changed"
                )
            witness_guard()
            value = getattr(witness, name)
            if _require_original_witness_contract is not witness_guard:
                raise LocalPacketBindingRejected(
                    "packet witness class lookup contract changed"
                )
            witness_guard()
            return value

        if (
            type(witness) is not _WITNESS_TYPE
            or type(read_witness("snapshot_sha256")) is not str
            or read_witness("snapshot_sha256") != expected["execution_snapshot_sha256"]
            or read_witness("packet_file_sha256") is not observed
            or read_witness("internal_packet_sha256") is not internal
            or any(read_witness(flag) is not False for flag in _DENIAL_FLAGS)
        ):
            raise LocalPacketBindingRejected("packet witness gained authority")
        unchanged()
        if (
            type(witness) is not _WITNESS_TYPE
            or read_witness("snapshot_sha256") != expected["execution_snapshot_sha256"]
            or read_witness("packet_file_sha256") is not observed
            or read_witness("internal_packet_sha256") is not internal
            or any(read_witness(flag) is not False for flag in _DENIAL_FLAGS)
        ):
            raise LocalPacketBindingRejected("packet witness changed after review")
        # A late false-valued denial getter may also replace a previously
        # inspected authority descriptor. Re-read every flag after the prior
        # pass; inspect all retained fields after the denial callbacks.
        unchanged()
        if (
            type(witness) is not _WITNESS_TYPE
            or read_witness("snapshot_sha256") != expected["execution_snapshot_sha256"]
            or read_witness("packet_file_sha256") is not observed
            or read_witness("internal_packet_sha256") is not internal
            or any(read_witness(flag) is not False for flag in _DENIAL_FLAGS)
        ):
            raise LocalPacketBindingRejected("packet witness changed in final review")
        unchanged()
        if (
            read_witness("snapshot_sha256") != expected["execution_snapshot_sha256"]
            or read_witness("packet_file_sha256") is not observed
            or read_witness("internal_packet_sha256") is not internal
            or any(read_witness(flag) is not False for flag in _DENIAL_FLAGS)
        ):
            raise LocalPacketBindingRejected("packet witness changed after final denial")
        # Field reads and denial getters are reflective callback boundaries.
        unchanged()
        if any(
            getattr(_WITNESS_TYPE, name) is not original
            for name, original in zip(
                _DENIAL_FLAGS, _ORIGINAL_DENIAL_DESCRIPTORS, strict=True,
            )
        ):
            raise LocalPacketBindingRejected(
                "packet witness denial descriptor changed"
            )
        return witness
    except (TypeError, KeyError, OverflowError, UnicodeError, RecursionError) as exc:
        raise LocalPacketBindingRejected("unreadable detached review packet") from exc
