"""Bounded, content-minimized READ result-set proof for disconnected fixtures.

Caller-provided results are NOT authenticated ToolBackend outputs. This never
reads the host, starts tools, authorizes actions or grants automatic replay.
Use only with an independently retained expected plan membership witness.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_REQ = re.compile(r"req_[0-9a-f]{32}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_OPS = frozenset(("math.sum", "text.stats", "text.find", "json.inspect"))
_DOMAIN = b"ARK-disconnected-complete-read-result-set-v1\0"
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_LOADS = json.loads
_MAX_STEP_BYTES = 8_192
_MAX_BATCH_BYTES = 65_536


class DisconnectedResultsRejected(ValueError):
    """Invalid, incomplete or mutated synthetic READ result collection."""


@dataclass(frozen=True, slots=True)
class DetachedReadResult:
    step_id: str
    operation: str
    canonical_result_json: str = field(repr=False)
    content_sha256: str


@dataclass(frozen=True, slots=True)
class CompleteDetachedReadResults:
    request_id: str
    step_ids: tuple[str, ...]
    result_count: int
    result_bytes: int
    membership_digest: str

    @property
    def external_result_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_RESULT_TYPE = DetachedReadResult
_SEALED_TYPE = CompleteDetachedReadResults
_RESULT_FIELDS = ("step_id", "operation", "canonical_result_json", "content_sha256")
_SEALED_FIELDS = ("request_id", "step_ids", "result_count", "result_bytes", "membership_digest")
_ORIGINAL_RESULT_DESCRIPTORS = tuple(vars(_RESULT_TYPE)[name] for name in _RESULT_FIELDS)
_ORIGINAL_SEALED_DESCRIPTORS = tuple(vars(_SEALED_TYPE)[name] for name in _SEALED_FIELDS)
_ORIGINAL_RESULT_INIT = vars(_RESULT_TYPE)["__init__"]
_ORIGINAL_SEALED_INIT = vars(_SEALED_TYPE)["__init__"]
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_RESULT_TYPE).get(name) for name in ("__new__", "__getattr__", "__getattribute__")
)
_ORIGINAL_SEALED_HOOKS = tuple(
    vars(_SEALED_TYPE).get(name) for name in ("__new__", "__getattr__", "__getattribute__")
)
_NONAUTHORITY_FLAGS = (
    "external_result_verified", "dispatch_authorized",
    "automatic_replay_authorized",
)
_NONAUTHORITY_DESCRIPTORS = tuple(
    vars(_SEALED_TYPE)[name] for name in _NONAUTHORITY_FLAGS
)


def _require_original_result_carriers() -> None:
    """Reject replaced constructors, fields and denial getters before invocation."""
    if (
        DetachedReadResult is not _RESULT_TYPE
        or CompleteDetachedReadResults is not _SEALED_TYPE
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or json.loads is not _ORIGINAL_LOADS
        or _pairs_unique is not _ORIGINAL_PAIRS_UNIQUE
        or _int64 is not _ORIGINAL_INT64
        or _no_float is not _ORIGINAL_NO_FLOAT
        or vars(_RESULT_TYPE).get("__init__") is not _ORIGINAL_RESULT_INIT
        or vars(_SEALED_TYPE).get("__init__") is not _ORIGINAL_SEALED_INIT
        or any(vars(_RESULT_TYPE).get(name) is not original for name, original in zip(
            _RESULT_FIELDS, _ORIGINAL_RESULT_DESCRIPTORS, strict=True,
        ))
        or any(vars(_SEALED_TYPE).get(name) is not original for name, original in zip(
            _SEALED_FIELDS, _ORIGINAL_SEALED_DESCRIPTORS, strict=True,
        ))
        or any(vars(_RESULT_TYPE).get(name) is not original for name, original in zip(
            ("__new__", "__getattr__", "__getattribute__"),
            _ORIGINAL_RESULT_HOOKS, strict=True,
        ))
        or any(vars(_SEALED_TYPE).get(name) is not original for name, original in zip(
            ("__new__", "__getattr__", "__getattribute__"),
            _ORIGINAL_SEALED_HOOKS, strict=True,
        ))
        or any(vars(_SEALED_TYPE).get(name) is not original for name, original in zip(
            _NONAUTHORITY_FLAGS, _NONAUTHORITY_DESCRIPTORS, strict=True,
        ))
    ):
        raise DisconnectedResultsRejected(
            "sealed READ result carrier or authority descriptor changed"
        )


def _pairs_unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise DisconnectedResultsRejected("duplicate JSON key")
        output[key] = value
    return output


def _int64(raw: str) -> int:
    number = int(raw)
    if not -(2**63) <= number < 2**63:
        raise DisconnectedResultsRejected("non-64-bit integer")
    return number


def _no_float(_: str) -> None:
    raise DisconnectedResultsRejected("float/nonfinite numbers forbidden")


_ORIGINAL_PAIRS_UNIQUE = _pairs_unique
_ORIGINAL_INT64 = _int64
_ORIGINAL_NO_FLOAT = _no_float


def _bounded_json(value: object, depth: int = 0) -> None:
    if depth > 12:
        raise DisconnectedResultsRejected("JSON nesting too deep")
    if type(value) is dict:
        if len(value) > 64:
            raise DisconnectedResultsRejected("JSON object too large")
        for key, item in value.items():
            _bounded_json(key, depth + 1)
            _bounded_json(item, depth + 1)
    elif type(value) is list:
        if len(value) > 128:
            raise DisconnectedResultsRejected("JSON array too large")
        for item in value:
            _bounded_json(item, depth + 1)
    elif type(value) is str:
        if len(value) > 8_192:
            raise DisconnectedResultsRejected("JSON text too large")
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise DisconnectedResultsRejected("invalid Unicode") from exc
    elif type(value) is int:
        if not -(2**63) <= value < 2**63:
            raise DisconnectedResultsRejected("unbounded integer")
    elif value is not None and type(value) is not bool:
        raise DisconnectedResultsRejected("unsupported JSON type")


def _verify_json(raw: str) -> bytes:
    _require_original_result_carriers()
    if type(raw) is not str:
        raise DisconnectedResultsRejected("result JSON must be an exact string")
    try:
        payload = raw.encode("utf-8", errors="strict")
        if not 0 < len(payload) <= _MAX_STEP_BYTES:
            raise DisconnectedResultsRejected("READ result byte budget exceeded")
        value = json.loads(
            raw, object_pairs_hook=_pairs_unique, parse_int=_int64,
            parse_float=_no_float, parse_constant=_no_float,
        )
        _require_original_result_carriers()
        _bounded_json(value)
        _require_original_result_carriers()
        normalized = json.dumps(
            value, sort_keys=True, ensure_ascii=True,
            allow_nan=False, separators=(",", ":"),
        )
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise DisconnectedResultsRejected("noncanonical result JSON") from exc
    _require_original_result_carriers()
    if raw != normalized:
        raise DisconnectedResultsRejected("result JSON must be canonical")
    return payload


def seal_detached_read_results(
    request_id: str,
    expected_steps: tuple[tuple[str, str], ...],
    results: tuple[DetachedReadResult, ...],
) -> CompleteDetachedReadResults:
    """Require exact entire expected READ membership, then build local digest.

    Expected steps MUST come from an independent plan witness; a malicious
    caller controlling both expected steps and results can forge this proof.
    This API returns no result contents and neither verifies execution nor
    automatically promotes a plan to a permission grant.
    """
    _require_original_result_carriers()
    if (
        type(request_id) is not str or _REQ.fullmatch(request_id) is None
        or type(expected_steps) is not tuple or not 1 <= len(expected_steps) <= 24
        or type(results) is not tuple or len(results) != len(expected_steps)
        or any(type(row) is not DetachedReadResult for row in results)
    ):
        raise DisconnectedResultsRejected("invalid expected READ result membership")
    original_request = request_id
    original_expected = expected_steps
    original_results = results
    captured_expected = tuple(expected_steps)
    captured_results = tuple(results)
    captured_fields = tuple(
        (row.step_id, row.operation, row.canonical_result_json, row.content_sha256)
        for row in captured_results
    )

    def epoch() -> None:
        _require_original_result_carriers()
        if (
            request_id is not original_request
            or expected_steps is not original_expected
            or results is not original_results
            or any(row is not old for row, old in zip(
                expected_steps, captured_expected, strict=True,
            ))
            or any(row is not old or any(now is not was for now, was in zip(
                (row.step_id, row.operation, row.canonical_result_json,
                 row.content_sha256), fields, strict=True,
            )) for row, old, fields in zip(
                results, captured_results, captured_fields, strict=True,
            ))
        ):
            raise DisconnectedResultsRejected("READ result carrier changed")

    epoch()
    seen: set[str] = set()
    validated = []
    total = 0
    for expected, _row, fields in zip(
        captured_expected, captured_results, captured_fields, strict=True,
    ):
        epoch()
        if type(expected) is not tuple or len(expected) != 2:
            raise DisconnectedResultsRejected("malformed expected step")
        step, operation = expected
        row_step, row_operation, raw, provided_hash = fields
        if (
            type(step) is not str or _STEP.fullmatch(step) is None
            or step in seen or type(operation) is not str or operation not in _OPS
            or row_step != step or row_operation != operation
            or type(row_step) is not str or type(row_operation) is not str
            or type(provided_hash) is not str or _SHA.fullmatch(provided_hash) is None
        ):
            raise DisconnectedResultsRejected("READ membership identity mismatch")
        seen.add(step)
        payload = _verify_json(raw)
        epoch()
        total += len(payload)
        if total > _MAX_BATCH_BYTES:
            raise DisconnectedResultsRejected("READ aggregate byte budget exceeded")
        computed_hash = hashlib.sha256(payload).hexdigest()
        epoch()
        if provided_hash != computed_hash:
            raise DisconnectedResultsRejected("READ content digest mismatch")
        validated.append((step, operation, provided_hash, len(payload)))
    epoch()
    manifest = json.dumps(
        {"request_id": request_id, "results": validated},
        sort_keys=True, ensure_ascii=True, separators=(",", ":"),
    )
    digest = hashlib.sha256(_DOMAIN + manifest.encode("ascii")).hexdigest()
    epoch()
    ids = tuple(row[0] for row in validated)
    sealed = _SEALED_TYPE(request_id, ids, len(ids), total, digest)
    pinned_sealed = (
        sealed.request_id, sealed.step_ids, sealed.result_count,
        sealed.result_bytes, sealed.membership_digest,
    )

    def sealed_epoch() -> None:
        _require_original_result_carriers()
        # A False-valued authority property is still a user-replaceable
        # callback. Check fields and original descriptors after EACH read.
        current = (
            sealed.request_id, sealed.step_ids, sealed.result_count,
            sealed.result_bytes, sealed.membership_digest,
        )
        if (
            type(sealed) is not _SEALED_TYPE
            or sealed.request_id is not request_id
            or sealed.step_ids is not ids
            or type(sealed.result_count) is not int
            or sealed.result_count != len(ids)
            or type(sealed.result_bytes) is not int
            or sealed.result_bytes != total
            or sealed.membership_digest is not digest
            or any(now is not before for now, before in zip(
                current, pinned_sealed, strict=True,
            ))
            or any(
                getattr(_SEALED_TYPE, name) is not original
                for name, original in zip(
                    _NONAUTHORITY_FLAGS, _NONAUTHORITY_DESCRIPTORS, strict=True,
                )
            )
        ):
            raise DisconnectedResultsRejected(
                "sealed READ result carrier or authority descriptor changed"
            )

    epoch()
    sealed_epoch()
    for flag in _NONAUTHORITY_FLAGS:
        if getattr(sealed, flag) is not False:
            raise DisconnectedResultsRejected("sealed READ result gained authority")
        sealed_epoch()
        epoch()
    sealed_epoch()
    epoch()
    return sealed
