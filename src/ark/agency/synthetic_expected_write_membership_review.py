"""Detached expected WRITE membership; no recovered bundle can self-attest completeness.

This is an isolated, disconnected prerequisite for future plan-wide recovery.
A caller must retain the witness independently of all per-WRITE archives and
SQLite files. The local hash detects corruption, not malicious re-signing.
No action, permission, clock or backend is available through this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_MAX_STEPS = 128
_MAX_STEP_CHARS = 256
_MAX_CANONICAL_BYTES = 40_000
_TOPOLOGY = re.compile(r"plan_[0-9a-f]{64}\Z")
_DIGEST = re.compile(r"expectedwrites_[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-independent-expected-write-membership-v1\0"


class SyntheticExpectedWriteMembershipRejected(RuntimeError):
    """Independent expected WRITE membership has not been established."""


@dataclass(frozen=True, slots=True)
class SyntheticExpectedWriteMembership:
    topology_digest: str
    step_ids: tuple[str, ...]
    digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def _validated_inputs(topology_digest: object, step_ids: object) -> bytes:
    if (
        type(topology_digest) is not str
        or _TOPOLOGY.fullmatch(topology_digest) is None
        or type(step_ids) is not tuple
        or not 1 <= len(step_ids) <= _MAX_STEPS
    ):
        raise SyntheticExpectedWriteMembershipRejected("invalid expected WRITE membership")
    for name in step_ids:
        if (
            type(name) is not str
            or not name.strip()
            or len(name) > _MAX_STEP_CHARS
        ):
            raise SyntheticExpectedWriteMembershipRejected("invalid WRITE step identity")
        try:
            name.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise SyntheticExpectedWriteMembershipRejected(
                "invalid WRITE step encoding"
            ) from exc
    if step_ids != tuple(sorted(set(step_ids))):
        raise SyntheticExpectedWriteMembershipRejected(
            "expected WRITE membership must be sorted and unique"
        )
    canonical = json.dumps(
        [topology_digest, list(step_ids)],
        separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    if len(canonical) > _MAX_CANONICAL_BYTES:
        raise SyntheticExpectedWriteMembershipRejected("membership evidence budget exceeded")
    return canonical


def _digest(payload: bytes) -> str:
    return "expectedwrites_" + hashlib.sha256(_DOMAIN + payload).hexdigest()


def capture_expected_write_membership(
    topology_digest: str,
    step_ids: tuple[str, ...],
) -> SyntheticExpectedWriteMembership:
    """Capture an independent topology's complete WRITE list before recovery.

    The caller, not this API, establishes that these IDs are all WRITEs in
    the original plan. Never construct this from the untrusted archive being
    checked; a self-derived list cannot detect an omitted archive entry.
    """
    original_topology, original_ids = topology_digest, step_ids
    canonical = _validated_inputs(original_topology, original_ids)
    if topology_digest is not original_topology or step_ids is not original_ids:
        raise SyntheticExpectedWriteMembershipRejected("expected membership changed")
    digest = _digest(canonical)
    if topology_digest is not original_topology or step_ids is not original_ids:
        raise SyntheticExpectedWriteMembershipRejected("expected membership changed")
    witness = SyntheticExpectedWriteMembership(
        original_topology, original_ids, digest,
    )
    assert_expected_write_membership(
        witness, topology_digest=original_topology, recovered_step_ids=original_ids,
    )
    if topology_digest is not original_topology or step_ids is not original_ids:
        raise SyntheticExpectedWriteMembershipRejected("expected membership changed")
    return witness


def assert_expected_write_membership(
    retained: SyntheticExpectedWriteMembership,
    *,
    topology_digest: str,
    recovered_step_ids: tuple[str, ...],
) -> None:
    """Fail closed if any detached WRITE archive was omitted or substituted.

    Only caller-retained independent evidence is admitted; neither a matching
    topology header nor a locally recomputed bundle digest is proof of the
    original plan's total WRITE membership or of an external action outcome.
    """
    if type(retained) is not SyntheticExpectedWriteMembership:
        raise SyntheticExpectedWriteMembershipRejected("exact retained witness required")
    original = (retained.topology_digest, retained.step_ids, retained.digest)
    observed = (topology_digest, recovered_step_ids)

    def assert_epoch() -> None:
        if (
            retained.topology_digest is not original[0]
            or retained.step_ids is not original[1]
            or retained.digest is not original[2]
            or topology_digest is not observed[0]
            or recovered_step_ids is not observed[1]
        ):
            raise SyntheticExpectedWriteMembershipRejected(
                "expected membership changed during review"
            )

    assert_epoch()
    canonical = _validated_inputs(original[0], original[1])
    assert_epoch()
    if type(original[2]) is not str or _DIGEST.fullmatch(original[2]) is None:
        raise SyntheticExpectedWriteMembershipRejected("invalid membership digest")
    if original[2] != _digest(canonical):
        raise SyntheticExpectedWriteMembershipRejected("membership witness digest mismatch")
    assert_epoch()
    _validated_inputs(observed[0], observed[1])
    assert_epoch()
    if observed[0] != original[0] or observed[1] != original[1]:
        raise SyntheticExpectedWriteMembershipRejected(
            "recovered WRITE membership differs from independent expected set"
        )
    assert_epoch()
