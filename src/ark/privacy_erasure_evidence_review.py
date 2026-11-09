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


# Preserve the denial implementation observed at module import. Capturing it
# inside review() would trust a preinstalled always-False replacement callback.
_ASSESSMENT_TYPE = SyntheticErasureAssessment
_AUTHORITY_NAMES = (
    "row_deletion_proven", "wal_reclamation_proven",
    "forensic_erasure_verified", "cleanup_authorized",
)
_ORIGINAL_AUTHORITY = tuple(
    vars(_ASSESSMENT_TYPE)[name] for name in _AUTHORITY_NAMES
)
# A frozen dataclass still exposes class-level slots and lookup hooks that
# can be rebound to a property before review reads its first input field.
_OBSERVATION_TYPE = SyntheticErasureObservations
_OBSERVATION_FIELDS = (
    "owner_scope_digest", "row_state", "reader_state", "checkpoint_state",
    "secure_delete_state", "backup_state", "wal_bytes_claimed",
)
_ASSESSMENT_FIELDS = (
    "evidence_digest", "blockers", "logical_absence_claimed",
)
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_OBSERVATION_CARRIER = tuple(
    vars(_OBSERVATION_TYPE).get(name)
    for name in (*_OBSERVATION_FIELDS, *_CARRIER_HOOKS)
)
_ORIGINAL_ASSESSMENT_CARRIER = tuple(
    vars(_ASSESSMENT_TYPE).get(name)
    for name in (*_ASSESSMENT_FIELDS, *_CARRIER_HOOKS)
)



# Treat serializer, domain, admissible vocabularies and regexp as exact
# diagnostic contracts. They receive caller privacy-scope identifiers and
# can otherwise be replaced with executable or overly permissive callbacks.
_ORIGINAL_ERASURE_HASHLIB = hashlib
_ORIGINAL_ERASURE_JSON = json
_ORIGINAL_ERASURE_SHA256 = hashlib.sha256
_ORIGINAL_ERASURE_DUMPS = json.dumps
_ORIGINAL_ERASURE_HEX = _HEX
_ORIGINAL_ERASURE_DOMAIN = _DOMAIN
_ORIGINAL_ERASURE_CHOICES = (
    _ROW, _READERS, _CHECKPOINT, _SECURE_DELETE, _BACKUPS,
)


def _assert_original_authority() -> None:
    if (
        hashlib is not _ORIGINAL_ERASURE_HASHLIB
        or json is not _ORIGINAL_ERASURE_JSON
        or hashlib.sha256 is not _ORIGINAL_ERASURE_SHA256
        or json.dumps is not _ORIGINAL_ERASURE_DUMPS
        or _HEX is not _ORIGINAL_ERASURE_HEX
        or _DOMAIN is not _ORIGINAL_ERASURE_DOMAIN
        or any(
            current is not original
            for current, original in zip(
                (_ROW, _READERS, _CHECKPOINT, _SECURE_DELETE, _BACKUPS),
                _ORIGINAL_ERASURE_CHOICES, strict=True,
            )
        )
    ):
        raise SyntheticErasureRejected(
            "erasure assessment digest implementation changed"
        )
    if (
        SyntheticErasureAssessment is not _ASSESSMENT_TYPE
        or SyntheticErasureObservations is not _OBSERVATION_TYPE
        or any(
            vars(_OBSERVATION_TYPE).get(name) is not original
            for name, original in zip(
                (*_OBSERVATION_FIELDS, *_CARRIER_HOOKS),
                _ORIGINAL_OBSERVATION_CARRIER, strict=True,
            )
        )
        or any(
            vars(_ASSESSMENT_TYPE).get(name) is not original
            for name, original in zip(
                (*_ASSESSMENT_FIELDS, *_CARRIER_HOOKS),
                _ORIGINAL_ASSESSMENT_CARRIER, strict=True,
            )
        )
        or any(
            vars(_ASSESSMENT_TYPE).get(name) is not original
            for name, original in zip(
                _AUTHORITY_NAMES, _ORIGINAL_AUTHORITY, strict=True,
            )
        )
    ):
        raise SyntheticErasureRejected(
            "erasure assessment authority descriptor changed"
        )


def review_synthetic_erasure_evidence(
    observations: SyntheticErasureObservations,
) -> SyntheticErasureAssessment:
    """Bounded diagnostic; neither row deletion nor data reclamation occurs."""
    if type(observations) is not SyntheticErasureObservations:
        raise SyntheticErasureRejected("exact erasure observations required")
    _assert_original_authority()
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
        _assert_original_authority()
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
    original_absence = epoch[1] == "absent"
    # Even an ORIGINAL property can become a callback boundary when hostile
    # __getattribute__ is injected on a fixture result. Recheck the pinned
    # denial descriptors BEFORE every subsequent getter; otherwise the first
    # getter could replace the second with executable, False-looking code.
    def assert_inert_result() -> None:
        def assert_result_carriers() -> None:
            if (
                type(result) is not SyntheticErasureAssessment
                or result.evidence_digest is not digest
                or result.blockers is not blocked
                or type(result.logical_absence_claimed) is not bool
                or result.logical_absence_claimed is not original_absence
            ):
                raise SyntheticErasureRejected(
                    "erasure assessment changed or acquired authority"
                )

        _assert_original_authority()
        assert_result_carriers()
        for name in _AUTHORITY_NAMES:
            _assert_original_authority()
            if getattr(result, name) is not False:
                raise SyntheticErasureRejected(
                    "erasure assessment changed or acquired authority"
                )
            # A getter can reflectively change the next property or a source
            # claim while still returning False. Stop before invoking another.
            _assert_original_authority()
            assert_epoch()
            assert_result_carriers()

    assert_epoch()
    assert_inert_result()
    assert_epoch()
    assert_inert_result()
    assert_epoch()
    return result
