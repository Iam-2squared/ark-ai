"""Detached verification of public-only diagnostic JSONL with caller-held bounds.

A matching chain detects accidental truncation/reordering/alteration relative to
caller-retained anchor, count, and tip. All claims are untrusted: not an audit
signature, independent storage witness, consent, or action authorization.
No filesystem, network, logging export, or mutation.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_DOMAIN = b"ARK-detached-private-diagnostics-v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_COMPONENT = frozenset((
    "memory", "planner", "privacy", "registry", "tool", "startup", "observation",
))
_STAGE = frozenset(("ingress", "preflight", "commit", "recovery", "postcheck"))
_OUTCOME = frozenset(("rejected", "deferred", "reviewed"))
_REASON = frozenset((
    "invalid_type", "stale", "conflict", "quota", "quarantined", "missing_evidence",
    "untrusted_claim", "integrity_mismatch", "nonreplay_required",
))
_KEYS = frozenset((
    "v", "seq", "component", "stage", "outcome", "reason", "prior", "sha256",
))
_MAX_EVENTS = 128
_MAX_SEQUENCE = 2**63 - 1
_MAX_BYTES = 50_000


class PrivateDiagnosticVerificationRejected(ValueError):
    """The untrusted public diagnostic transcript failed exact verification."""


@dataclass(frozen=True, slots=True)
class PrivateDiagnosticVerification:
    first_sequence: int
    last_sequence: int
    count: int
    final_sha256: str

    @property
    def audit_authenticated(self) -> bool:
        return False

    @property
    def cleanup_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False

    @property
    def private_data_export_authorized(self) -> bool:
        return False


_RESULT_TYPE = PrivateDiagnosticVerification
_RESULT_FIELDS = ("first_sequence", "last_sequence", "count", "final_sha256")
_RESULT_DENIALS = (
    "audit_authenticated", "cleanup_authorized",
    "tool_execution_authorized", "private_data_export_authorized",
)
_RESULT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT = tuple(vars(_RESULT_TYPE).get(n) for n in (
    *_RESULT_FIELDS, *_RESULT_DENIALS, *_RESULT_HOOKS,
))
_ORIGINAL_JSON = json
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_LOADS = json.loads
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_SHA = _SHA
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_COMPONENT = _COMPONENT
_ORIGINAL_STAGE = _STAGE
_ORIGINAL_OUTCOME = _OUTCOME
_ORIGINAL_REASON = _REASON
_ORIGINAL_KEYS = _KEYS
_ORIGINAL_LIMITS = (_MAX_EVENTS, _MAX_SEQUENCE, _MAX_BYTES)


def _require_original_protocol() -> None:
    # Preaccess guard: no private caller bytes or anchor reach a replaced
    # parser/hash callback. Same-process code cannot be made a security sandbox.
    if (
        PrivateDiagnosticVerification is not _RESULT_TYPE
        or any(vars(_RESULT_TYPE).get(n) is not original for n, original in zip(
            (*_RESULT_FIELDS, *_RESULT_DENIALS, *_RESULT_HOOKS),
            _ORIGINAL_RESULT, strict=True,
        ))
        or json is not _ORIGINAL_JSON
        or hashlib is not _ORIGINAL_HASHLIB
        or json.dumps is not _ORIGINAL_DUMPS
        or json.loads is not _ORIGINAL_LOADS
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or _SHA is not _ORIGINAL_SHA
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _COMPONENT is not _ORIGINAL_COMPONENT
        or _STAGE is not _ORIGINAL_STAGE
        or _OUTCOME is not _ORIGINAL_OUTCOME
        or _REASON is not _ORIGINAL_REASON
        or _KEYS is not _ORIGINAL_KEYS
        or type(_MAX_EVENTS) is not int
        or type(_MAX_SEQUENCE) is not int
        or type(_MAX_BYTES) is not int
        or (_MAX_EVENTS, _MAX_SEQUENCE, _MAX_BYTES) != _ORIGINAL_LIMITS
    ):
        raise PrivateDiagnosticVerificationRejected(
            "diagnostic verifier protocol or authority descriptor changed"
        )


def verify_private_diagnostic_jsonl(
    canonical_jsonl: str,
    *,
    retained_anchor_sha256: str,
    expected_start_sequence: int,
    expected_count: int,
    expected_final_sha256: str,
) -> PrivateDiagnosticVerification:
    """Verify exact public-code JSONL and the caller-retained length and tip.

    Reject unknown keys, duplicate keys, reordered keys, noncanonical numbers,
    invalid code values, gaps, altered bytes, and truncated/suffixed chains.
    The anchor/count/tip must come from a separately retained source to be
    useful, but this function cannot establish that source's authenticity.
    """
    _require_original_protocol()
    if (
        type(canonical_jsonl) is not str
        or not 1 <= len(canonical_jsonl) <= _MAX_BYTES
        or type(retained_anchor_sha256) is not str
        or _SHA.fullmatch(retained_anchor_sha256) is None
        or type(expected_final_sha256) is not str
        or _SHA.fullmatch(expected_final_sha256) is None
        or type(expected_start_sequence) is not int
        or not 1 <= expected_start_sequence <= _MAX_SEQUENCE
        or type(expected_count) is not int
        or not 1 <= expected_count <= _MAX_EVENTS
        or expected_start_sequence > _MAX_SEQUENCE - expected_count + 1
    ):
        raise PrivateDiagnosticVerificationRejected("invalid retained diagnostic envelope")
    try:
        encoded = canonical_jsonl.encode("ascii")
    except UnicodeEncodeError as exc:
        raise PrivateDiagnosticVerificationRejected(
            "diagnostic JSONL must be ASCII"
        ) from exc
    if len(encoded) > _MAX_BYTES or not canonical_jsonl.endswith("\n"):
        raise PrivateDiagnosticVerificationRejected("diagnostic JSONL bounds invalid")
    lines = canonical_jsonl[:-1].split("\n")
    if len(lines) != expected_count or any(not line for line in lines):
        raise PrivateDiagnosticVerificationRejected("diagnostic record count mismatch")

    chain = retained_anchor_sha256
    for i, line in enumerate(lines):
        _require_original_protocol()
        try:
            row = json.loads(line)
        except (ValueError, TypeError, RecursionError) as exc:
            raise PrivateDiagnosticVerificationRejected(
                "diagnostic JSONL record malformed"
            ) from exc
        _require_original_protocol()
        if (
            type(row) is not dict or frozenset(row) != _KEYS
            or type(row["v"]) is not int or row["v"] != 1
            or type(row["seq"]) is not int
            or row["seq"] != expected_start_sequence + i
            or any(
                type(row[name]) is not str or row[name] not in accepted
                for name, accepted in (
                    ("component", _COMPONENT), ("stage", _STAGE),
                    ("outcome", _OUTCOME), ("reason", _REASON),
                )
            )
            or type(row["prior"]) is not str or row["prior"] != chain
            or type(row["sha256"]) is not str
            or _SHA.fullmatch(row["sha256"]) is None
        ):
            raise PrivateDiagnosticVerificationRejected("diagnostic record content invalid")
        canonical = json.dumps(
            row, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
        )
        _require_original_protocol()
        if canonical != line:
            raise PrivateDiagnosticVerificationRejected("noncanonical diagnostic JSONL")
        data = [
            1, row["seq"], row["component"], row["stage"],
            row["outcome"], row["reason"], chain,
        ]
        material = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        _require_original_protocol()
        calculated = hashlib.sha256(_DOMAIN + material.encode("ascii")).hexdigest()
        _require_original_protocol()
        if calculated != row["sha256"]:
            raise PrivateDiagnosticVerificationRejected("diagnostic chain mismatch")
        chain = calculated
    if chain != expected_final_sha256:
        raise PrivateDiagnosticVerificationRejected("retained diagnostic tip mismatch")
    _require_original_protocol()
    result = PrivateDiagnosticVerification(
        expected_start_sequence, expected_start_sequence + expected_count - 1,
        expected_count, chain,
    )
    _require_original_protocol()
    for name in _RESULT_DENIALS:
        _require_original_protocol()
        if getattr(result, name) is not False:
            raise PrivateDiagnosticVerificationRejected(
                "diagnostic verification acquired authority"
            )
        _require_original_protocol()
    return result
