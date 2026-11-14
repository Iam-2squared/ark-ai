"""Deterministic memory-only READ fixture tools; no external dispatch.

This intentionally does not implement ToolBackend and cannot satisfy a
PermissionGate, trusted clock, consent, or real-world execution requirement.
It handles caller-supplied synthetic JSON, performs no I/O, and is reversible.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import re
from dataclasses import dataclass, field

_ID = re.compile(r"req_[0-9a-f]{32}\Z")
_OPERATIONS = frozenset(("math.sum", "text.stats", "text.find", "json.inspect"))
_DOMAIN = b"ARK-disconnected-toolbox-v1\0"
_MAX_INPUT = 16_384
_MAX_TEXT = 8_192
_MAX_DEPTH = 16
_MIN_INT = -(2**63)
_MAX_INT = 2**63 - 1


_ORIGINAL_BUILTINS = builtins
_ORIGINAL_SUM = builtins.sum
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_JSON_LOADS = json.loads
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_ID = _ID
_ORIGINAL_OPERATIONS = _OPERATIONS
_ORIGINAL_LIMITS = (_MAX_INPUT, _MAX_TEXT, _MAX_DEPTH, _MIN_INT, _MAX_INT)


class DisconnectedToolRejected(ValueError):
    """Malformed, mutated or unsafe disconnected tool fixture."""


@dataclass(frozen=True, slots=True)
class DisconnectedToolRequest:
    request_id: str
    operation: str
    canonical_args_json: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class DisconnectedToolResult:
    request_id: str
    operation: str
    input_digest: str
    canonical_result_json: str = field(repr=False)
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


# A disconnected result must never turn into a capability/dispatch receipt,
# even when a result property is monkeypatched to return False until queried.
_REQUEST_TYPE = DisconnectedToolRequest
_RESULT_TYPE = DisconnectedToolResult
_REQUEST_FIELDS = ("request_id", "operation", "canonical_args_json")
_RESULT_FIELDS = (
    "request_id", "operation", "input_digest", "canonical_result_json",
    "result_digest",
)
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REQUEST_SLOTS = tuple(
    vars(_REQUEST_TYPE).get(name) for name in _REQUEST_FIELDS + _CARRIER_HOOKS
)
_ORIGINAL_RESULT_SLOTS = tuple(
    vars(_RESULT_TYPE).get(name) for name in _RESULT_FIELDS + _CARRIER_HOOKS
)
_DENIAL_NAMES = (
    "dispatch_authorized", "automatic_replay_authorized",
    "external_outcome_known",
)
_ORIGINAL_DENIALS = tuple(vars(_RESULT_TYPE)[key] for key in _DENIAL_NAMES)


def _require_original_fixture_primitives() -> None:
    # Reject a preinstalled SHA/JSON callback BEFORE passing caller-private
    # synthetic arguments to it. Recheck after every calculation boundary.
    # This establishes only local implementation identity, not attestation.
    if (
        builtins is not _ORIGINAL_BUILTINS
        or builtins.sum is not _ORIGINAL_SUM
        # Python resolves unqualified sum() in _run through module globals
        # before builtins. A synthetic injected global must not receive
        # private fixture numbers even while builtins.sum remains original.
        or "sum" in globals()
        or hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.loads is not _ORIGINAL_JSON_LOADS
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _ID is not _ORIGINAL_ID
        or _OPERATIONS is not _ORIGINAL_OPERATIONS
        or any(type(value) is not int for value in
               (_MAX_INPUT, _MAX_TEXT, _MAX_DEPTH, _MIN_INT, _MAX_INT))
        or (_MAX_INPUT, _MAX_TEXT, _MAX_DEPTH, _MIN_INT, _MAX_INT)
           != _ORIGINAL_LIMITS
        or any(globals()[name] is not original
               for name, original in _ORIGINAL_HELPERS.items())
    ):
        raise DisconnectedToolRejected(
            "disconnected fixture digest or JSON implementation changed"
        )


def _require_original_request_carrier() -> None:
    # A frozen request is still executable if its class-level field/lookup
    # descriptors are replaced. Inspect the class BEFORE reading private JSON.
    if (
        DisconnectedToolRequest is not _REQUEST_TYPE
        or any(
            vars(_REQUEST_TYPE).get(name) is not original
            for name, original in zip(
                _REQUEST_FIELDS + _CARRIER_HOOKS,
                _ORIGINAL_REQUEST_SLOTS, strict=True,
            )
        )
    ):
        raise DisconnectedToolRejected(
            "disconnected fixture request descriptor changed"
        )


def _require_original_result_denials() -> None:
    # Check constructor and field hooks as well as False-only properties.
    # A synthetic callback can rebind them before result construction or
    # between return checks; fail closed before any result field is read.
    if (
        DisconnectedToolResult is not _RESULT_TYPE
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RESULT_FIELDS + _CARRIER_HOOKS,
                _ORIGINAL_RESULT_SLOTS, strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(key) is not expected
            for key, expected in zip(
                _DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True,
            )
        )
    ):
        raise DisconnectedToolRejected(
            "disconnected fixture authority definition changed"
        )


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
    _require_original_fixture_primitives()
    try:
        parsed = json.loads(
            raw,
            object_pairs_hook=_unique_pairs,
            parse_int=_integer,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
        _require_original_fixture_primitives()
        return parsed
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise DisconnectedToolRejected("invalid canonical JSON") from exc


def _canonical(value: object) -> str:
    _require_original_fixture_primitives()
    try:
        encoded = json.dumps(
            value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
            allow_nan=False,
        )
        _require_original_fixture_primitives()
        return encoded
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


# A nested JSON hook, validator or tool-function replacement could otherwise
# receive decoded caller-private arguments despite the top-level SHA/JSON pin.
# These exact helpers never dispatch; replacing them is not a supported API.
_ORIGINAL_HELPERS = {
    name: globals()[name]
    for name in (
        "_unique_pairs", "_integer", "_reject_number", "_json", "_canonical",
        "_text", "_validate_tree", "_run",
    )
}


def execute_disconnected_fixture_tool(
    request: DisconnectedToolRequest,
) -> DisconnectedToolResult:
    """Perform only deterministic, bounded, unprivileged in-memory calculations.

    The returned value is a test fixture, never evidence that a ToolBackend
    executed or that a real-world action occurred. Inputs are exact canonical
    JSON to avoid implicit coercions, duplicate keys and ambiguous identity.
    """
    _require_original_fixture_primitives()
    _require_original_request_carrier()
    _require_original_result_denials()
    if type(request) is not DisconnectedToolRequest:
        raise DisconnectedToolRejected("exact request type required")
    pinned = (request.request_id, request.operation, request.canonical_args_json)

    def assert_epoch() -> None:
        _require_original_fixture_primitives()
        _require_original_request_carrier()
        _require_original_result_denials()
        if any(
            current is not original
            for current, original in zip(
                (request.request_id, request.operation, request.canonical_args_json),
                pinned, strict=True,
            )
        ):
            raise DisconnectedToolRejected("request changed during fixture execution")

    request_id, operation, raw = pinned
    # Bound fixed-width synthetic identities and operation names before the
    # regex engine or set lookup. Neither path dispatches an external tool.
    if (
        type(request_id) is not str or len(request_id) != 36
        or _ID.fullmatch(request_id) is None
        or type(operation) is not str or len(operation) > 12
        or operation not in _OPERATIONS
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
    _require_original_result_denials()
    result = DisconnectedToolResult(
        request_id, operation, input_digest, data, result_digest,
    )
    # A reentrant result constructor may mutate the request/result class.
    # Recheck before touching the constructed receipt.
    assert_epoch()
    if (
        type(result) is not _RESULT_TYPE
        or result.request_id is not request_id
        or result.operation is not operation
        or result.input_digest is not input_digest
        or result.canonical_result_json is not data
        or result.result_digest is not result_digest
    ):
        raise DisconnectedToolRejected("constructed fixture result changed")
    # A false-looking property can itself be a caller-controlled callback
    # that rewrites a frozen receipt or replaces another authority property.
    for denial in _DENIAL_NAMES:
        assert_epoch()
        if getattr(result, denial) is not False:
            raise DisconnectedToolRejected("disconnected fixture gained authority")
        assert_epoch()
        if (
            type(result) is not _RESULT_TYPE
            or result.request_id is not request_id
            or result.operation is not operation
            or result.input_digest is not input_digest
            or result.canonical_result_json is not data
            or result.result_digest is not result_digest
        ):
            raise DisconnectedToolRejected(
                "disconnected fixture result changed during denial check"
            )
    return result
