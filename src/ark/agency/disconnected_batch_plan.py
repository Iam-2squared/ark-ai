"""Pure fixture-only batch planning; never dispatches or validates an action grant.

Independent of ToolBackend, the in-flight disconnected executor, model I/O,
network and host filesystem effects. A local digest is not an attestation.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_REQUEST_ID = re.compile(r"req_[0-9a-f]{32}\Z")
_STEP_ID = re.compile(r"step_[0-9a-f]{16}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ALLOWED = frozenset(("math.sum", "text.stats", "text.find", "json.inspect"))
_DOMAIN = b"ARK-detached-disconnected-batch-v1\0"
_MAX_STEPS = 24
_MAX_ARG_BYTES = 4_096
_MAX_TOTAL_BYTES = 20_480


class DisconnectedBatchRejected(ValueError):
    """A detached fixture is noncanonical, mutated, oversized or incomplete."""


@dataclass(frozen=True, slots=True)
class DisconnectedBatchStep:
    step_id: str
    operation: str
    canonical_args_json: str = field(repr=False)
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DisconnectedBatchPlan:
    request_id: str
    steps: tuple[DisconnectedBatchStep, ...]
    canonical_plan_json: str = field(repr=False)
    plan_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def replay_authorized(self) -> bool:
        return False

    @property
    def execution_proven(self) -> bool:
        return False


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise DisconnectedBatchRejected("duplicate JSON key")
        output[key] = value
    return output


def _no_fraction(_: str) -> None:
    raise DisconnectedBatchRejected("floating or nonfinite JSON is unsupported")


def _parse_integer(value: str) -> int:
    number = int(value)
    if not -(2**63) <= number < 2**63:
        raise DisconnectedBatchRejected("unbounded integer")
    return number


def _validate_json(value: object, depth: int = 0) -> None:
    if depth > 12:
        raise DisconnectedBatchRejected("JSON depth budget exceeded")
    if type(value) is dict:
        if len(value) > 64:
            raise DisconnectedBatchRejected("JSON object budget exceeded")
        for key, item in value.items():
            _validate_json(key, depth + 1)
            _validate_json(item, depth + 1)
    elif type(value) is list:
        if len(value) > 128:
            raise DisconnectedBatchRejected("JSON array budget exceeded")
        for item in value:
            _validate_json(item, depth + 1)
    elif type(value) is str:
        if len(value) > 4_096:
            raise DisconnectedBatchRejected("JSON string budget exceeded")
        try:
            value.encode("utf-8", "strict")
        except UnicodeError as exc:
            raise DisconnectedBatchRejected("invalid Unicode") from exc
    elif type(value) is int:
        if not -(2**63) <= value < 2**63:
            raise DisconnectedBatchRejected("unbounded integer")
    elif value is not None and type(value) is not bool:
        raise DisconnectedBatchRejected("unsupported JSON value")


def _arguments(raw: str) -> None:
    if type(raw) is not str:
        raise DisconnectedBatchRejected("arguments must be canonical JSON text")
    try:
        encoded = raw.encode("utf-8", "strict")
        if not 0 < len(encoded) <= _MAX_ARG_BYTES:
            raise DisconnectedBatchRejected("argument byte budget exceeded")
        parsed = json.loads(
            raw, object_pairs_hook=_unique_pairs,
            parse_int=_parse_integer, parse_float=_no_fraction,
            parse_constant=_no_fraction,
        )
        if type(parsed) is not dict:
            raise DisconnectedBatchRejected("arguments must be a JSON object")
        _validate_json(parsed)
        canonical = json.dumps(
            parsed, sort_keys=True, ensure_ascii=True, allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise DisconnectedBatchRejected("invalid bounded canonical JSON") from exc
    if canonical != raw:
        raise DisconnectedBatchRejected("arguments are not canonical")


def _make_payload(
    request_id: str, steps: tuple[DisconnectedBatchStep, ...],
) -> str:
    if (
        type(request_id) is not str or _REQUEST_ID.fullmatch(request_id) is None
        or type(steps) is not tuple or not 1 <= len(steps) <= _MAX_STEPS
    ):
        raise DisconnectedBatchRejected("invalid batch identity or size")
    seen: set[str] = set()
    rows: list[dict[str, object]] = []
    total = 0
    for step in steps:
        if type(step) is not DisconnectedBatchStep:
            raise DisconnectedBatchRejected("exact step type required")
        name, operation, raw, dependencies = (
            step.step_id, step.operation, step.canonical_args_json, step.depends_on,
        )
        if (
            type(name) is not str or _STEP_ID.fullmatch(name) is None
            or name in seen or type(operation) is not str or operation not in _ALLOWED
            or type(dependencies) is not tuple or len(dependencies) > 16
            or any(type(item) is not str for item in dependencies)
            or tuple(sorted(set(dependencies))) != dependencies
            or any(item not in seen for item in dependencies)
        ):
            raise DisconnectedBatchRejected("duplicate, unsafe or forward-dependent step")
        _arguments(raw)
        total += len(raw.encode("utf-8"))
        if total > _MAX_TOTAL_BYTES:
            raise DisconnectedBatchRejected("batch arguments budget exceeded")
        rows.append({
            "step_id": name, "operation": operation,
            "canonical_args_json": raw, "depends_on": dependencies,
        })
        seen.add(name)
    result = json.dumps(
        {"request_id": request_id, "steps": rows},
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    )
    if len(result.encode("utf-8")) > 32_768:
        raise DisconnectedBatchRejected("batch manifest budget exceeded")
    return result


def _epoch(
    steps: tuple[DisconnectedBatchStep, ...],
    carriers: tuple[tuple[object, ...], ...],
    original_steps: tuple[DisconnectedBatchStep, ...],
) -> None:
    if (
        len(steps) != len(original_steps)
        or any(
            current is not previous or any(
                field is not old for field, old in zip(
                    (current.step_id, current.operation, current.canonical_args_json,
                     current.depends_on), fields, strict=True,
                )
            )
            for current, previous, fields in zip(
                steps, original_steps, carriers, strict=True,
            )
        )
    ):
        raise DisconnectedBatchRejected("batch step mutated during review")


def build_disconnected_batch_plan(
    request_id: str, steps: tuple[DisconnectedBatchStep, ...],
) -> DisconnectedBatchPlan:
    """Construct a bounded immutable PLAN, never execute any of its steps."""
    original_id = request_id
    original_steps = steps
    if type(steps) is not tuple:
        raise DisconnectedBatchRejected("exact step tuple required")
    original_records = tuple(steps)
    pinned = tuple((s.step_id, s.operation, s.canonical_args_json, s.depends_on)
                   for s in steps if type(s) is DisconnectedBatchStep)
    if len(pinned) != len(steps):
        raise DisconnectedBatchRejected("exact step type required")
    payload = _make_payload(request_id, steps)
    _epoch(steps, pinned, original_records)
    digest = hashlib.sha256(_DOMAIN + payload.encode("utf-8")).hexdigest()
    _epoch(steps, pinned, original_records)
    result = DisconnectedBatchPlan(request_id, steps, payload, digest)
    if (
        request_id is not original_id or steps is not original_steps
        or type(result) is not DisconnectedBatchPlan
        or result.request_id is not original_id
        or result.steps is not original_steps
        or result.canonical_plan_json is not payload
        or result.plan_digest is not digest
    ):
        raise DisconnectedBatchRejected("batch identity changed during construction")
    _epoch(steps, pinned, original_records)
    return result


def verify_disconnected_batch_plan(
    plan: DisconnectedBatchPlan, *, retained_digest: str,
) -> None:
    """Revalidate a local manifest against an INDEPENDENTLY retained digest.

    An attacker able to rewrite both the plan and retained digest can still
    forge this check; the digest is not signed authorization or trusted storage.
    """
    if (
        type(plan) is not DisconnectedBatchPlan
        or type(retained_digest) is not str or _SHA.fullmatch(retained_digest) is None
    ):
        raise DisconnectedBatchRejected("exact plan and retained digest required")
    initial = (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest)
    original_records = tuple(plan.steps) if type(plan.steps) is tuple else ()
    pinned = tuple((s.step_id, s.operation, s.canonical_args_json, s.depends_on)
                   for s in original_records if type(s) is DisconnectedBatchStep)

    def check_epoch() -> None:
        if any(
            actual is not prior for actual, prior in zip(
                (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest),
                initial, strict=True,
            )
        ):
            raise DisconnectedBatchRejected("batch plan mutated during verification")
        _epoch(plan.steps, pinned, original_records)

    check_epoch()
    actual = _make_payload(plan.request_id, plan.steps)
    check_epoch()
    computed = hashlib.sha256(_DOMAIN + actual.encode("utf-8")).hexdigest()
    check_epoch()
    if (
        type(plan.canonical_plan_json) is not str or plan.canonical_plan_json != actual
        or type(plan.plan_digest) is not str or plan.plan_digest != computed
        or computed != retained_digest
    ):
        raise DisconnectedBatchRejected("detached batch integrity mismatch")
    check_epoch()
