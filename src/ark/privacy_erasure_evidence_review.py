"""No-I/O diagnostic for untrusted SQLite privacy erasure observations.

Never treats logical deletion, a completed WAL checkpoint, secure_delete, or
caller testimony as forensic-erasure proof. Does not read or mutate files.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-privacy-erasure-evidence-v1\0"
_ROW = frozenset(("present", "absent", "unknown"))
_READERS = frozenset(("active", "none_claimed", "unknown"))
_CHECKPOINT = frozenset(("busy", "complete_claimed", "not_run", "unknown"))
_SECURE_DELETE = frozenset(("on_claimed", "off", "unknown"))
_BACKUPS = frozenset(("exist", "none_claimed", "unknown"))


class SyntheticErasureRejected(ValueError):
    """Untrusted or malformed erasure evidence cannot be classified."""


@dataclass(frozen=True, slots=True)
class SyntheticErasureObservations:
    owner_scope_digest: str
    row_state: str
    reader_state: str
    checkpoint_state: str
    secure_delete_state: str
    backup_state: str
    wal_bytes_claimed: int | None


@dataclass(frozen=True, slots=True)
class SyntheticErasureAssessment:
    evidence_digest: str
    blockers: tuple[str, ...]
    logical_absence_claimed: bool

    @property
    def row_deletion_proven(self) -> bool:
        return False

    @property
    def wal_reclamation_proven(self) -> bool:
        return False

    @property
    def forensic_erasure_verified(self) -> bool:
        return False

    @property
    def cleanup_authorized(self) -> bool:
        return False


def review_synthetic_erasure_evidence(
    observations: SyntheticErasureObservations,
) -> SyntheticErasureAssessment:
    """Bounded diagnostic; neither row deletion nor data reclamation occurs."""
    if type(observations) is not SyntheticErasureObservations:
        raise SyntheticErasureRejected("exact erasure observations required")
    names = (
        "owner_scope_digest", "row_state", "reader_state", "checkpoint_state",
        "secure_delete_state", "backup_state", "wal_bytes_claimed",
    )
    epoch = tuple(getattr(observations, name) for name in names)
    if (
        type(epoch[0]) is not str or _HEX.fullmatch(epoch[0]) is None
        or type(epoch[1]) is not str or epoch[1] not in _ROW
        or type(epoch[2]) is not str or epoch[2] not in _READERS
        or type(epoch[3]) is not str or epoch[3] not in _CHECKPOINT
        or type(epoch[4]) is not str or epoch[4] not in _SECURE_DELETE
        or type(epoch[5]) is not str or epoch[5] not in _BACKUPS
        or epoch[6] is not None and (type(epoch[6]) is not int or not 0 <= epoch[6] <= 2**63-1)
    ):
        raise SyntheticErasureRejected("malformed erasure observations")

    def assert_epoch() -> None:
        if type(observations) is not SyntheticErasureObservations or any(
            getattr(observations, name) is not prior
            for name, prior in zip(names, epoch, strict=True)
        ):
            raise SyntheticErasureRejected("erasure observations changed during review")

    assert_epoch()
    payload = json.dumps(list(epoch), separators=(",", ":"), allow_nan=False).encode()
    assert_epoch()
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    assert_epoch()
    blockers = ["independent_storage_attestation_missing"]
    if epoch[1] != "absent":
        blockers.append("row_absence_unestablished")
    if epoch[2] != "none_claimed":
        blockers.append("reader_snapshot_may_retain_bytes")
    if epoch[3] != "complete_claimed":
        blockers.append("wal_checkpoint_not_confirmed")
    if epoch[6] is None or epoch[6] != 0:
        blockers.append("wal_bytes_not_confirmed_zero")
    if epoch[4] != "on_claimed":
        blockers.append("secure_delete_policy_unconfirmed")
    if epoch[5] != "none_claimed":
        blockers.append("backup_or_snapshot_exposure_unresolved")
    # Even an optimistic caller-reported local observation is NOT proof.
    blockers.append("forensic_scope_not_attested")
    blocked = tuple(blockers)
    result = SyntheticErasureAssessment(digest, blocked, epoch[1] == "absent")
    assert_epoch()
    if (
        type(result) is not SyntheticErasureAssessment
        or result.evidence_digest is not digest
        or result.blockers is not blocked
    ):
        raise SyntheticErasureRejected("erasure assessment changed during construction")
    return result
