"""Strict bounded JSON review of disconnected, synthetic V3 preflight evidence.

This fixture-only parser binds *the actual supplied packet bytes* to the
existing detached numerical cross-check. No file, GPU, Candidate, training,
owner approval, provider or protected evaluation is opened or authorized.
Local SHA-256 is not an authenticated provenance or runtime receipt.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from ark import v3_detached_preflight_crossbind as crossbind

_MAX_BYTES = 4096
_TOP = frozenset(("snapshot", "evidence"))
_SNAPSHOT = frozenset((
    "device", "capacity_gib", "tokenizer_probe_sha256",
    "wall_clock_timeout_minutes",
))
_EVIDENCE = frozenset((
    "device", "reported_capacity_gib", "tokenizer_probe_sha256",
    "peak_vram_mib", "peak_reserved_vram_mib", "wall_seconds",
))


class DetachedV3PacketRejected(ValueError):
    """An untrusted offline V3 evidence packet is not reproducible or safe."""


@dataclass(frozen=True, slots=True)
class DetachedV3PacketReview:
    packet_sha256: str
    crossbind_digest: str
    checks: tuple[str, ...]

    @property
    def paid_compute_authorized(self) -> bool:
        return False

    @property
    def training_authorized(self) -> bool:
        return False

    @property
    def candidate_promotion_authorized(self) -> bool:
        return False

    @property
    def provenance_authenticated(self) -> bool:
        return False


_REPORT = DetachedV3PacketReview
_REPORT_FIELDS = ("packet_sha256", "crossbind_digest", "checks")
_DENIALS = (
    "paid_compute_authorized", "training_authorized",
    "candidate_promotion_authorized", "provenance_authenticated",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_FIELDS = tuple(
    vars(_REPORT).get(k) for k in (*_REPORT_FIELDS, *_DENIALS, *_HOOKS)
)
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_LOADS = json.loads
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_CROSSBIND = crossbind.review_detached_v3_preflight
_ORIGINAL_CROSSBIND_PROTOCOL = crossbind._protocol
_ORIGINAL_CLASSES = (
    crossbind.DetachedV3Snapshot, crossbind.DetachedV3Evidence,
    crossbind.DetachedV3PreflightReview,
)
_ORIGINAL_LIMIT = _MAX_BYTES
_ORIGINAL_TOP = _TOP
_ORIGINAL_SNAPSHOT = _SNAPSHOT
_ORIGINAL_EVIDENCE = _EVIDENCE


def _protocol() -> None:
    # Refuse replacement control-plane callbacks before invoking any of them.
    if crossbind._protocol is not _ORIGINAL_CROSSBIND_PROTOCOL:
        raise DetachedV3PacketRejected("detached V3 packet protocol changed")
    _ORIGINAL_CROSSBIND_PROTOCOL()
    if (
        _protocol is not _ORIGINAL_PROTOCOL
        or _pairs_unique is not _ORIGINAL_PAIRS_UNIQUE
        or _nonfinite is not _ORIGINAL_NONFINITE
        or _fields is not _ORIGINAL_FIELDS_HELPER
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.loads is not _ORIGINAL_LOADS
        or json.dumps is not _ORIGINAL_DUMPS
        or crossbind.review_detached_v3_preflight is not _ORIGINAL_CROSSBIND
        or (
            crossbind.DetachedV3Snapshot, crossbind.DetachedV3Evidence,
            crossbind.DetachedV3PreflightReview,
        ) != _ORIGINAL_CLASSES
        or type(_MAX_BYTES) is not int or _MAX_BYTES != _ORIGINAL_LIMIT
        or _TOP is not _ORIGINAL_TOP
        or _SNAPSHOT is not _ORIGINAL_SNAPSHOT
        or _EVIDENCE is not _ORIGINAL_EVIDENCE
        or DetachedV3PacketReview is not _REPORT
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(
                (*_REPORT_FIELDS, *_DENIALS, *_HOOKS),
                _ORIGINAL_FIELDS, strict=True,
            )
        )
    ):
        raise DetachedV3PacketRejected("detached V3 packet protocol changed")


def _pairs_unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise DetachedV3PacketRejected("duplicate V3 JSON key")
        out[key] = value
    return out


def _nonfinite(value: str) -> None:
    raise DetachedV3PacketRejected("nonfinite V3 JSON number")


def _fields(value: object, keys: frozenset[str]) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise DetachedV3PacketRejected("unexpected or missing V3 packet field")
    return value


# Freeze strict JSON policy callbacks before inspecting arbitrary packet bytes.
_ORIGINAL_PAIRS_UNIQUE = _pairs_unique
_ORIGINAL_NONFINITE = _nonfinite
_ORIGINAL_FIELDS_HELPER = _fields
_ORIGINAL_PROTOCOL = _protocol


def review_detached_v3_packet(packet: bytes) -> DetachedV3PacketReview:
    """Review exact canonical UTF-8 JSON bytes with no side effects.

    Duplicate object keys, unknown/missing fields, nonfinite numbers and
    noncanonical serialization fail closed. A passing result NEVER approves
    costs, training, candidate promotion or independent provenance.
    """
    _ORIGINAL_PROTOCOL()
    if type(packet) is not bytes or not 1 <= len(packet) <= _MAX_BYTES:
        raise DetachedV3PacketRejected("exact bounded V3 packet bytes required")
    try:
        payload = json.loads(
            packet.decode("utf-8", errors="strict"),
            object_pairs_hook=_pairs_unique,
            parse_constant=_nonfinite,
        )
    except (ValueError, TypeError, UnicodeError, OverflowError) as exc:
        raise DetachedV3PacketRejected("invalid strict V3 packet JSON") from exc
    data = _fields(payload, _TOP)
    snapshot_fields = _fields(data["snapshot"], _SNAPSHOT)
    evidence_fields = _fields(data["evidence"], _EVIDENCE)
    # Hash actual supplied bytes, not a partial packet or a pre-hash JSON
    # structure with the digest added later. Strict canonical bytes prevent
    # ambiguous whitespace/order spellings from masquerading as one packet.
    if json.dumps(
        data, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii") != packet:
        raise DetachedV3PacketRejected("noncanonical V3 packet byte representation")
    _ORIGINAL_PROTOCOL()
    try:
        snapshot = crossbind.DetachedV3Snapshot(**snapshot_fields)
        evidence = crossbind.DetachedV3Evidence(**evidence_fields)
        review = crossbind.review_detached_v3_preflight(snapshot, evidence)
    except (TypeError, ValueError) as exc:
        raise DetachedV3PacketRejected("invalid V3 evidence cross-binding") from exc
    _ORIGINAL_PROTOCOL()
    if (
        type(review) is not crossbind.DetachedV3PreflightReview
        or review.independent_provenance_verified is not False
        or review.training_authorized is not False
        or review.paid_compute_authorized is not False
        or review.candidate_promotion_authorized is not False
    ):
        raise DetachedV3PacketRejected("detached V3 review gained authority")
    packet_sha = hashlib.sha256(packet).hexdigest()
    expected_checks = (
        "device", "capacity", "tokenizer_probe", "peak_vram_order",
        "wall_clock_budget",
    )
    _ORIGINAL_PROTOCOL()
    if (
        type(review.digest) is not str or len(review.digest) != 64
        or review.checks != expected_checks
    ):
        raise DetachedV3PacketRejected("detached V3 cross-binding result changed")
    result = _REPORT(packet_sha, review.digest, expected_checks)
    _ORIGINAL_PROTOCOL()
    if (
        type(result) is not _REPORT
        or result.packet_sha256 != packet_sha
        or result.crossbind_digest != review.digest
        or result.checks != expected_checks
        or any(getattr(result, name) is not False for name in _DENIALS)
    ):
        raise DetachedV3PacketRejected("detached V3 packet result gained authority")
    _ORIGINAL_PROTOCOL()
    return result
