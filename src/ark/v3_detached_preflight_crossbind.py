"""Free-only, detached consistency review of *synthetic* V3 preflight evidence.

No Candidate runtime, GPU, filesystem, provider, approval issuer or protected
evaluation is opened. This optional review does not modify or replace the
frozen V3 preflight contract on Draft PR #5. It rejects discrepancies; passing
it is NOT provenance, cost authorization, training approval or promotion.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-detached-V3-preflight-crossbind-v1\0"
_MAX_BYTES = 4_096


class DetachedV3PreflightRejected(ValueError):
    """An unauthenticated cross-binding or numerical evidence check failed."""


@dataclass(frozen=True, slots=True)
class DetachedV3Snapshot:
    device: str
    capacity_gib: float
    tokenizer_probe_sha256: str
    wall_clock_timeout_minutes: int


@dataclass(frozen=True, slots=True)
class DetachedV3Evidence:
    device: str
    reported_capacity_gib: float
    tokenizer_probe_sha256: str
    peak_vram_mib: float
    peak_reserved_vram_mib: float
    wall_seconds: float


@dataclass(frozen=True, slots=True)
class DetachedV3PreflightReview:
    digest: str
    checks: tuple[str, ...]

    @property
    def independent_provenance_verified(self) -> bool:
        return False

    @property
    def training_authorized(self) -> bool:
        return False

    @property
    def paid_compute_authorized(self) -> bool:
        return False

    @property
    def candidate_promotion_authorized(self) -> bool:
        return False


_SNAPSHOT = DetachedV3Snapshot
_EVIDENCE = DetachedV3Evidence
_REVIEW = DetachedV3PreflightReview
_FIELDS = {
    _SNAPSHOT: ("device", "capacity_gib", "tokenizer_probe_sha256",
                "wall_clock_timeout_minutes"),
    _EVIDENCE: ("device", "reported_capacity_gib", "tokenizer_probe_sha256",
                "peak_vram_mib", "peak_reserved_vram_mib", "wall_seconds"),
}
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_SLOTS = {
    cls: tuple(vars(cls).get(field) for field in fields + _HOOKS)
    for cls, fields in _FIELDS.items()
}
_REVIEW_FIELDS = ("digest", "checks") + _HOOKS
_ORIGINAL_REVIEW_FIELDS = tuple(vars(_REVIEW).get(n) for n in _REVIEW_FIELDS)
_ORIGINAL_MAX_BYTES = _MAX_BYTES
_DENIALS = (
    "independent_provenance_verified", "training_authorized",
    "paid_compute_authorized", "candidate_promotion_authorized",
)
_ORIGINAL_DENIALS = tuple(vars(_REVIEW)[field] for field in _DENIALS)
_ORIGINAL_SHA = _SHA
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_FIELDS_MAP = _FIELDS
_ORIGINAL_FIELD_ITEMS = tuple(_FIELDS.items())
_ORIGINAL_HOOKS = _HOOKS
_ORIGINAL_SLOTS_MAP = _ORIGINAL_SLOTS
_ORIGINAL_SLOT_TUPLES = tuple((cls, _ORIGINAL_SLOTS[cls]) for cls in _FIELDS)
_ORIGINAL_DENIAL_NAMES = _DENIALS
_ORIGINAL_REVIEW_FIELD_NAMES = _REVIEW_FIELDS
_ORIGINAL_MATH_MODULE = math
_ORIGINAL_MATH_ISFINITE = math.isfinite


def _protocol() -> None:
    if (
        DetachedV3Snapshot is not _SNAPSHOT
        or DetachedV3Evidence is not _EVIDENCE
        or DetachedV3PreflightReview is not _REVIEW
        or _SHA is not _ORIGINAL_SHA
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or hashlib.sha256 is not _ORIGINAL_HASH
        or json.dumps is not _ORIGINAL_DUMPS
        or type(_MAX_BYTES) is not int or _MAX_BYTES != _ORIGINAL_MAX_BYTES
        or _FIELDS is not _ORIGINAL_FIELDS_MAP
        or tuple(_FIELDS) != tuple(cls for cls, _ in _ORIGINAL_FIELD_ITEMS)
        or any(
            _FIELDS.get(cls) is not fields
            for cls, fields in _ORIGINAL_FIELD_ITEMS
        )
        or _HOOKS is not _ORIGINAL_HOOKS
        or _ORIGINAL_SLOTS is not _ORIGINAL_SLOTS_MAP
        or any(
            _ORIGINAL_SLOTS.get(cls) is not slots
            for cls, slots in _ORIGINAL_SLOT_TUPLES
        )
        or _DENIALS is not _ORIGINAL_DENIAL_NAMES
        or _REVIEW_FIELDS is not _ORIGINAL_REVIEW_FIELD_NAMES
        or math is not _ORIGINAL_MATH_MODULE
        or math.isfinite is not _ORIGINAL_MATH_ISFINITE
        # This detached reviewer must not call a rebinding of its own local
        # device/digest/numeric validators on frozen-like private evidence.
        or any(
            now is not original
            for now, original in zip(
                (_numeric, _device, _digest), _ORIGINAL_VALIDATORS, strict=True,
            )
        )
        or any(
            vars(_REVIEW).get(name) is not old
            for name, old in zip(
                _REVIEW_FIELDS, _ORIGINAL_REVIEW_FIELDS, strict=True,
            )
        )
        or any(
            vars(cls).get(field) is not value
            for cls, fields in _FIELDS.items()
            for field, value in zip(
                fields + _HOOKS, _ORIGINAL_SLOTS[cls], strict=True,
            )
        )
        or any(
            vars(_REVIEW).get(field) is not value
            for field, value in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise DetachedV3PreflightRejected("detached V3 review protocol changed")


def _numeric(value: object) -> float:
    if type(value) not in (int, float):
        raise DetachedV3PreflightRejected("nonexact V3 numeric evidence")
    try:
        number = float(value)
    except (ValueError, OverflowError) as exc:
        raise DetachedV3PreflightRejected("unrepresentable V3 number") from exc
    if not math.isfinite(number) or number <= 0:
        raise DetachedV3PreflightRejected("nonfinite or nonpositive V3 number")
    # A huge integer could otherwise round to another integer on conversion
    # to float and spuriously match a different capacity/measurement.
    if type(value) is int and int(number) != value:
        raise DetachedV3PreflightRejected("precision-losing V3 integer")
    return number


def _device(value: object) -> str:
    if (
        type(value) is not str or not 1 <= len(value) <= 128
        or value != value.strip()
        or any(ord(c) < 33 or ord(c) > 126 for c in value)
    ):
        raise DetachedV3PreflightRejected("invalid exact V3 device identity")
    return value


def _digest(value: object) -> str:
    if type(value) is not str or _SHA.fullmatch(value) is None:
        raise DetachedV3PreflightRejected("invalid V3 tokenizer probe digest")
    return value


_ORIGINAL_VALIDATORS = (_numeric, _device, _digest)


def review_detached_v3_preflight(
    snapshot: DetachedV3Snapshot,
    evidence: DetachedV3Evidence,
) -> DetachedV3PreflightReview:
    """Reject contradictory synthetic preflight values without executing V3."""
    _protocol()
    if type(snapshot) is not _SNAPSHOT or type(evidence) is not _EVIDENCE:
        raise DetachedV3PreflightRejected("exact detached V3 carriers required")

    pinned = tuple(getattr(snapshot, name) for name in _FIELDS[_SNAPSHOT])
    retained = tuple(getattr(evidence, name) for name in _FIELDS[_EVIDENCE])

    def stable() -> None:
        _protocol()
        if (
            any(
                getattr(snapshot, name) is not old
                for name, old in zip(_FIELDS[_SNAPSHOT], pinned, strict=True)
            )
            or any(
                getattr(evidence, name) is not old
                for name, old in zip(_FIELDS[_EVIDENCE], retained, strict=True)
            )
        ):
            raise DetachedV3PreflightRejected("detached V3 evidence changed")

    stable()
    device, capacity, tokenizer, budget = pinned
    measured_device, measured_capacity, probe, allocated, reserved, wall = retained
    if _device(device) != _device(measured_device):
        raise DetachedV3PreflightRejected("device not bound to frozen runtime")
    if _digest(tokenizer) != _digest(probe):
        raise DetachedV3PreflightRejected("tokenizer probe not bound to snapshot")
    capacity_gib = _numeric(capacity)
    measured_gib = _numeric(measured_capacity)
    allocated_mib = _numeric(allocated)
    reserved_mib = _numeric(reserved)
    wall_seconds = _numeric(wall)
    if type(budget) is not int or not 1 <= budget <= 1_000_000:
        raise DetachedV3PreflightRejected("invalid frozen wall-clock budget")
    # Intentionally exact: this detached conservative reviewer invents no
    # tolerance/measurement confidence interval for the frozen V3 gate.
    if capacity_gib != measured_gib:
        raise DetachedV3PreflightRejected("capacity not bound to runtime")
    capacity_mib = capacity_gib * 1024.0
    timeout_seconds = budget * 60
    if (
        not math.isfinite(capacity_mib)
        or not 0 < allocated_mib <= reserved_mib <= capacity_mib
        or wall_seconds > timeout_seconds
    ):
        raise DetachedV3PreflightRejected("VRAM ordering or time budget violated")
    stable()
    payload = (
        device, capacity_gib, tokenizer, budget, measured_device,
        measured_gib, probe, allocated_mib, reserved_mib, wall_seconds,
    )
    data = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    stable()
    if len(data) > _MAX_BYTES:
        raise DetachedV3PreflightRejected("detached V3 metadata budget exceeded")
    digest = hashlib.sha256(_DOMAIN + data.encode("ascii")).hexdigest()
    stable()
    result = _REVIEW(
        digest,
        ("device", "capacity", "tokenizer_probe", "peak_vram_order",
         "wall_clock_budget"),
    )
    stable()
    if (
        type(result) is not _REVIEW
        or type(result.digest) is not str
        or result.digest != digest
        or type(result.checks) is not tuple
        or result.checks != (
            "device", "capacity", "tokenizer_probe", "peak_vram_order",
            "wall_clock_budget",
        )
    ):
        raise DetachedV3PreflightRejected("detached V3 review result changed")
    for denial in _DENIALS:
        stable()
        if getattr(result, denial) is not False:
            raise DetachedV3PreflightRejected("detached V3 result gained authority")
    stable()
    return result
