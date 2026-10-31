"""Resolve bounded, synthetic earlier-READ result references without dispatch.

The caller supplies all results and retained digests; these are neither an
execution receipt nor authenticated provenance. No filesystem/network/OS/tool
operation, Memory access, eval, or model call occurs in this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_REQUEST = re.compile(r"req_[0-9a-f]{32}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-detached-synthetic-read-binding-v1\0"
_MAX_STEPS = 24
_MAX_JSON = 8_192
_MAX_OUTPUT = 4_096
_MAX_DEPTH = 12


class ReadBindingRejected(ValueError):
    """An offline fixture reference is ambiguous, missing or unsafe."""


@dataclass(frozen=True, slots=True)
class SyntheticReadResult:
    step_id: str
    canonical_result_json: str = field(repr=False)
    retained_digest: str


@dataclass(frozen=True, slots=True)
class SyntheticBoundArguments:
    request_id: str
    used_step_ids: tuple[str, ...]
    canonical_args_json: str = field(repr=False)
    binding_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def replay_authorized(self) -> bool:
        return False

    @property
    def external_result_proven(self) -> bool:
        return False


def _pairs_unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ReadBindingRejected("duplicate JSON key")
        value[key] = item
    return value


def _no_float(_: str) -> None:
    raise ReadBindingRejected("floating-point JSON unsupported")


def _integer(raw: str) -> int:
    value = int(raw)
    if not -(2**63) <= value < 2**63:
        raise ReadBindingRejected("integer budget exceeded")
    return value


def _validate(value: object, depth: int = 0) -> None:
    if depth > _MAX_DEPTH:
        raise ReadBindingRejected("JSON depth budget exceeded")
    if type(value) is dict:
        if len(value) > 64:
            raise ReadBindingRejected("object member budget exceeded")
        for key, item in value.items():
            _validate(key, depth + 1)
            _validate(item, depth + 1)
    elif type(value) is list:
        if len(value) > 128:
            raise ReadBindingRejected("array member budget exceeded")
        for item in value:
            _validate(item, depth + 1)
    elif type(value) is str:
        if len(value) > 4_096:
            raise ReadBindingRejected("string budget exceeded")
        try:
            value.encode("utf-8", "strict")
        except UnicodeError as exc:
            raise ReadBindingRejected("invalid Unicode") from exc
    elif type(value) is int:
        if not -(2**63) <= value < 2**63:
            raise ReadBindingRejected("integer budget exceeded")
    elif value is not None and type(value) is not bool:
        raise ReadBindingRejected("unsupported JSON type")


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True,
        allow_nan=False, separators=(",", ":"),
    )


def _load(raw: str, *, root_object: bool) -> object:
    if type(raw) is not str:
        raise ReadBindingRejected("exact JSON text required")
    try:
        encoded = raw.encode("utf-8", "strict")
        if not 0 < len(encoded) <= _MAX_JSON:
            raise ReadBindingRejected("JSON byte budget exceeded")
        value = json.loads(
            raw, object_pairs_hook=_pairs_unique, parse_int=_integer,
            parse_float=_no_float, parse_constant=_no_float,
        )
        if root_object and type(value) is not dict:
            raise ReadBindingRejected("argument root must be a JSON object")
        _validate(value)
        if _canonical(value) != raw:
            raise ReadBindingRejected("noncanonical JSON")
        return value
    except (TypeError, ValueError, RecursionError, UnicodeError) as exc:
        raise ReadBindingRejected("invalid bounded JSON fixture") from exc


def read_result_digest(step_id: str, canonical_result_json: str) -> str:
    """Compute a *local* fixture digest; it does not prove Tool execution."""
    if type(step_id) is not str or _STEP.fullmatch(step_id) is None:
        raise ReadBindingRejected("invalid READ step ID")
    _load(canonical_result_json, root_object=False)
    return hashlib.sha256(
        _DOMAIN + step_id.encode("ascii") + b"\0"
        + canonical_result_json.encode("ascii")
    ).hexdigest()


def _pointer(root: object, pointer: str) -> object:
    if type(pointer) is not str or len(pointer) > 128:
        raise ReadBindingRejected("invalid result pointer")
    if pointer == "":
        return root
    if not pointer.startswith("/") or pointer.count("/") > 12:
        raise ReadBindingRejected("invalid result pointer")
    value = root
    for token in pointer.split("/")[1:]:
        if re.search(r"~(?![01])", token):
            raise ReadBindingRejected("noncanonical pointer escaping")
        token = token.replace("~1", "/").replace("~0", "~")
        if type(value) is dict and token in value:
            value = value[token]
        elif type(value) is list and re.fullmatch(r"0|[1-9][0-9]*", token):
            index = int(token)
            if index >= len(value):
                raise ReadBindingRejected("result index out of range")
            value = value[index]
        else:
            raise ReadBindingRejected("missing result pointer")
    return value


def bind_synthetic_read_arguments(
    request_id: str,
    canonical_template_json: str,
    earlier_step_ids: tuple[str, ...],
    results: tuple[SyntheticReadResult, ...],
) -> SyntheticBoundArguments:
    """Substitute exact earlier-step JSON pointers into detached arguments.

    The caller must retain plan membership independently; a local digest
    cannot establish a trusted graph, consent, or a successful external READ.
    """
    if (
        type(request_id) is not str or _REQUEST.fullmatch(request_id) is None
        or type(earlier_step_ids) is not tuple
        or not 0 <= len(earlier_step_ids) <= _MAX_STEPS
        or len(set(earlier_step_ids)) != len(earlier_step_ids)
        or any(type(s) is not str or _STEP.fullmatch(s) is None
               for s in earlier_step_ids)
        or type(results) is not tuple or len(results) > _MAX_STEPS
        or any(type(row) is not SyntheticReadResult for row in results)
    ):
        raise ReadBindingRejected("invalid detached plan prefix")
    original = (request_id, canonical_template_json, earlier_step_ids, results)
    pinned = tuple((row, row.step_id, row.canonical_result_json, row.retained_digest)
                   for row in results)

    def assert_epoch() -> None:
        if any(now is not before for now, before in zip(
            (request_id, canonical_template_json, earlier_step_ids, results),
            original, strict=True,
        )) or any(
            results[i] is not row
            or row.step_id is not name
            or row.canonical_result_json is not raw
            or row.retained_digest is not digest
            for i, (row, name, raw, digest) in enumerate(pinned)
        ):
            raise ReadBindingRejected("READ binding fixture changed")

    assert_epoch()
    order = {step: i for i, step in enumerate(earlier_step_ids)}
    parsed: dict[str, object] = {}
    digest_by_id: dict[str, str] = {}
    last_order = -1
    for _row, name, raw, expected in pinned:
        assert_epoch()
        if (
            type(name) is not str or name not in order
            or order[name] <= last_order
            or type(expected) is not str or _SHA.fullmatch(expected) is None
            or read_result_digest(name, raw) != expected
        ):
            raise ReadBindingRejected("out-of-prefix, unordered, or forged READ fixture")
        parsed[name] = _load(raw, root_object=False)
        digest_by_id[name] = expected
        last_order = order[name]
        assert_epoch()

    template = _load(canonical_template_json, root_object=True)
    used: set[str] = set()

    def resolve(value: object, depth: int) -> object:
        if depth > _MAX_DEPTH:
            raise ReadBindingRejected("template depth budget exceeded")
        if type(value) is dict:
            if "$from" in value:
                if set(value) != {"$from"} or type(value["$from"]) is not dict:
                    raise ReadBindingRejected("ambiguous reference marker")
                ref = value["$from"]
                if set(ref) != {"step_id", "pointer"}:
                    raise ReadBindingRejected("malformed result reference")
                step = ref["step_id"]
                if type(step) is not str or step not in parsed:
                    raise ReadBindingRejected("forward or missing READ reference")
                used.add(step)
                return _pointer(parsed[step], ref["pointer"])
            return {key: resolve(item, depth + 1) for key, item in value.items()}
        if type(value) is list:
            return [resolve(item, depth + 1) for item in value]
        return value

    assert_epoch()
    resolved = resolve(template, 0)
    _validate(resolved)
    raw_out = _canonical(resolved)
    if len(raw_out.encode("ascii")) > _MAX_OUTPUT:
        raise ReadBindingRejected("resolved arguments too large")
    assert_epoch()
    selected = tuple(step for step in earlier_step_ids if step in used)
    provenance = _canonical({
        "request_id": request_id, "template": canonical_template_json,
        "prior_results": [(step, digest_by_id[step]) for step in selected],
        "resolved": raw_out,
    })
    digest = hashlib.sha256(_DOMAIN + provenance.encode("ascii")).hexdigest()
    assert_epoch()
    result = SyntheticBoundArguments(request_id, selected, raw_out, digest)
    assert_epoch()
    if (
        result.request_id is not request_id
        or result.used_step_ids != selected
        or result.canonical_args_json is not raw_out
        or result.binding_digest is not digest
    ):
        raise ReadBindingRejected("result changed before return")
    return result
