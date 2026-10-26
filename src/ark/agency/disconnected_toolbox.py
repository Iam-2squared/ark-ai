"""Deterministic memory-only READ fixture tools; no external dispatch.

This intentionally does not implement ToolBackend and cannot satisfy a
PermissionGate, trusted clock, consent, or real-world execution requirement.
It handles caller-supplied synthetic JSON, performs no I/O, and is reversible.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_ID = re.compile(r"req_[0-9a-f]{32}\Z")
_OPERATIONS = frozenset(("math.sum", "text.stats", "text.find", "json.inspect"))
_DOMAIN = b"ARK-disconnected-toolbox-v1\0"
_MAX_INPUT = 16_384
_MAX_TEXT = 8_192
_MAX_DEPTH = 16
_MIN_INT = -(2**63)
_MAX_INT = 2**63 - 1


class DisconnectedToolRejected(ValueError):
    """Malformed, mutated or unsafe disconnected tool fixture."""


@dataclass(frozen=True, slots=True)
class DisconnectedToolRequest:
    request_id: str
    operation: str
    canonical_args_json: str


@dataclass(frozen=True, slots=True)
class DisconnectedToolResult:
    request_id: str
    operation: str
    input_digest: str
    canonical_result_json: str
    result_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DisconnectedToolRejected("duplicate JSON key")
        result[key] = value
    return result


def _integer(raw: str) -> int:
    value = int(raw)
    if not _MIN_INT <= value <= _MAX_INT:
        raise DisconnectedToolRejected("JSON integer outside signed 64-bit bounds")
    return value


def _reject_number(_: str) -> None:
    raise DisconnectedToolRejected("floating-point and nonfinite JSON are unsupported")


def _json(raw: str) -> object:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_unique_pairs,
            parse_int=_integer,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise DisconnectedToolRejected("invalid canonical JSON") from exc


def _canonical(value: object) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise DisconnectedToolRejected("invalid JSON value") from exc


def _text(value: object) -> str:
    if type(value) is not str or len(value) > _MAX_TEXT:
        raise DisconnectedToolRejected("invalid bounded text")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise DisconnectedToolRejected("invalid Unicode text") from exc
    return value


def _validate_tree(value: object, depth: int = 0) -> None:
    if depth > _MAX_DEPTH:
        raise DisconnectedToolRejected("JSON nesting exceeds budget")
    if type(value) is dict:
        if len(value) > 128:
            raise DisconnectedToolRejected("JSON object exceeds budget")
        for key, item in value.items():
            _text(key)
            _validate_tree(item, depth + 1)
    elif type(value) is list:
        if len(value) > 128:
            raise DisconnectedToolRejected("JSON array exceeds budget")
        for item in value:
            _validate_tree(item, depth + 1)
    elif type(value) is str:
        _text(value)
    elif type(value) is int:
        if not _MIN_INT <= value <= _MAX_INT:
            raise DisconnectedToolRejected("JSON integer outside signed 64-bit bounds")
    elif value is not None and type(value) is not bool:
        raise DisconnectedToolRejected("unsupported JSON type")


def _run(operation: str, args: object) -> dict[str, object]:
    if type(args) is not dict:
        raise DisconnectedToolRejected("tool arguments must be an object")
    if operation == "math.sum":
        if set(args) != {"values"} or type(args["values"]) is not list:
            raise DisconnectedToolRejected("math.sum requires values list")
        values = args["values"]
        if not 1 <= len(values) <= 128 or any(type(item) is not int for item in values):
            raise DisconnectedToolRejected("math.sum requires bounded exact integers")
        total = sum(values)
        if not _MIN_INT <= total <= _MAX_INT:
            raise DisconnectedToolRejected("integer sum overflow")
        return {"count": len(values), "sum": total}
    if operation == "text.stats":
        if set(args) != {"text"}:
            raise DisconnectedToolRejected("text.stats requires text")
        value = _text(args["text"])
        return {
            "characters": len(value),
            "lines": len(value.splitlines()),
            "words": len(value.split()),
        }
    if operation == "text.find":
        if set(args) != {"text", "needle"}:
            raise DisconnectedToolRejected("text.find requires text and needle")
        content, needle = _text(args["text"]), _text(args["needle"])
        if not needle:
            raise DisconnectedToolRejected("empty search needle")
        return {"index": content.find(needle)}
    if operation == "json.inspect":
        if set(args) != {"json"}:
            raise DisconnectedToolRejected("json.inspect requires JSON text")
        content = _text(args["json"])
        parsed = _json(content)
        _validate_tree(parsed)
        if _canonical(parsed) != content:
            raise DisconnectedToolRejected("embedded JSON is not canonical")
        kind = "object" if type(parsed) is dict else "array" if type(parsed) is list else "scalar"
        return {"kind": kind, "items": len(parsed) if type(parsed) in (dict, list) else 1}
    raise DisconnectedToolRejected("tool operation unavailable")


def execute_disconnected_fixture_tool(
    request: DisconnectedToolRequest,
) -> DisconnectedToolResult:
    """Perform only deterministic, bounded, unprivileged in-memory calculations.

    The returned value is a test fixture, never evidence that a ToolBackend
    executed or that a real-world action occurred. Inputs are exact canonical
    JSON to avoid implicit coercions, duplicate keys and ambiguous identity.
    """
    if type(request) is not DisconnectedToolRequest:
        raise DisconnectedToolRejected("exact request type required")
    pinned = (request.request_id, request.operation, request.canonical_args_json)

    def assert_epoch() -> None:
        if any(
            current is not original
            for current, original in zip(
                (request.request_id, request.operation, request.canonical_args_json),
                pinned, strict=True,
            )
        ):
            raise DisconnectedToolRejected("request changed during fixture execution")

    request_id, operation, raw = pinned
    if (
        type(request_id) is not str or _ID.fullmatch(request_id) is None
        or type(operation) is not str or operation not in _OPERATIONS
        or type(raw) is not str or not 0 < len(raw) <= _MAX_INPUT
    ):
        raise DisconnectedToolRejected("unsupported or unbounded fixture request")
    try:
        raw_bytes = raw.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise DisconnectedToolRejected("invalid fixture encoding") from exc
    if len(raw_bytes) > _MAX_INPUT:
        raise DisconnectedToolRejected("fixture byte budget exceeded")
    args = _json(raw)
    _validate_tree(args)
    if _canonical(args) != raw:
        raise DisconnectedToolRejected("tool argument JSON is not canonical")
    assert_epoch()
    data = _canonical(_run(operation, args))
    if len(data.encode("utf-8")) > _MAX_INPUT:
        raise DisconnectedToolRejected("fixture result budget exceeded")
    assert_epoch()
    input_digest = hashlib.sha256(_DOMAIN + raw_bytes).hexdigest()
    assert_epoch()
    result_digest = hashlib.sha256(
        _DOMAIN + operation.encode("ascii") + b"\0" + data.encode("utf-8")
    ).hexdigest()
    assert_epoch()
    result = DisconnectedToolResult(
        request_id, operation, input_digest, data, result_digest,
    )
    assert_epoch()
    if (
        type(result) is not DisconnectedToolResult
        or result.request_id is not request_id
        or result.operation is not operation
        or result.input_digest is not input_digest
        or result.canonical_result_json is not data
        or result.result_digest is not result_digest
    ):
        raise DisconnectedToolRejected("constructed fixture result changed")
    return result
