"""Offline, deny-only task-lane selector for CI-independent ARK groundwork.

Selection is a proposed diagnostic schedule, not verified CI evidence,
spending approval, GitHub write permission, or autonomous execution authority.
All budget, approval, path and gate inputs are caller assertions, untrusted.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields

_MAX_LANES = 128
_MAX_SELECTED = 5
_LABEL = re.compile(r"[a-zA-Z0-9_.:-]{1,128}\Z")
_PATH_COMPONENT = re.compile(r"[a-zA-Z0-9_.-]{1,120}\Z")
_COSTS = frozenset(("free_local", "potentially_billable", "unknown"))
_DOMAIN = b"ARK-disconnected-work-lane-selector-v1\0"


class SyntheticLaneSelectionRejected(RuntimeError):
    """The input work graph or claimed safety boundary is malformed."""


@dataclass(frozen=True, slots=True)
class SyntheticWorkLane:
    lane_id: str
    priority: int
    touches: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    requires_green: tuple[str, ...] = ()
    cost_class: str = "unknown"
    requires_approval: bool = True
    reversible: bool = False


@dataclass(frozen=True, slots=True)
class SyntheticLaneSelection:
    selected: tuple[str, ...]
    deferred: tuple[tuple[str, str], ...]
    diagnostic_digest: str

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def github_write_authorized(self) -> bool:
        return False

    @property
    def spending_authorized(self) -> bool:
        return False


# A synthetic callback must not replace the original denial-only result type.
_SELECTION_RESULT_TYPE = SyntheticLaneSelection


def _check_label(label: object) -> bool:
    return type(label) is str and _LABEL.fullmatch(label) is not None


def _check_path(path: object) -> bool:
    if type(path) is not str or len(path) > 256 or "\\" in path:
        return False
    parts = path.split("/")
    return bool(parts) and all(
        _PATH_COMPONENT.fullmatch(part) is not None
        and part not in (".", "..")
        and not part.startswith(".")
        for part in parts
    )


def _check_labels(values: object, *, paths: bool = False) -> bool:
    if type(values) is not tuple or len(values) > 16:
        return False
    checker = _check_path if paths else _check_label
    return all(checker(item) for item in values) and values == tuple(sorted(set(values)))


def _overlap(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


# Work lanes are caller-provided diagnostics.  No monkeypatched JSON/hash,
# parser, overlap check or class descriptor may inspect private path claims
# before the original implementation is verified.
_ORIGINAL_HASHLIB_MODULE = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_MODULE = json
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_FIELDS_FUNCTION = fields
_ORIGINAL_PATTERNS = (_LABEL, _PATH_COMPONENT)
_ORIGINAL_COSTS = _COSTS
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_LIMITS = (_MAX_LANES, _MAX_SELECTED)
_ORIGINAL_HELPERS = (_check_label, _check_path, _check_labels, _overlap)
_LANE_TYPE = SyntheticWorkLane
_LANE_FIELDS = (
    "lane_id", "priority", "touches", "depends_on", "requires_green",
    "cost_class", "requires_approval", "reversible",
)
_RESULT_FIELDS = ("selected", "deferred", "diagnostic_digest")
_RESULT_DENIALS = (
    "execution_authorized", "github_write_authorized", "spending_authorized",
)
_LOOKUP_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_LANE_DESCRIPTORS = tuple(
    vars(_LANE_TYPE).get(name) for name in _LANE_FIELDS + _LOOKUP_HOOKS
)
_ORIGINAL_RESULT_DESCRIPTORS = tuple(
    vars(_SELECTION_RESULT_TYPE).get(name)
    for name in _RESULT_FIELDS + _RESULT_DENIALS + _LOOKUP_HOOKS
)


def _require_original_lane_selection_protocol() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB_MODULE
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON_MODULE
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or fields is not _ORIGINAL_FIELDS_FUNCTION
        or (_LABEL is not _ORIGINAL_PATTERNS[0])
        or (_PATH_COMPONENT is not _ORIGINAL_PATTERNS[1])
        or _COSTS is not _ORIGINAL_COSTS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or (_MAX_LANES, _MAX_SELECTED) != _ORIGINAL_LIMITS
        or (_check_label, _check_path, _check_labels, _overlap)
        != _ORIGINAL_HELPERS
        or SyntheticWorkLane is not _LANE_TYPE
        or SyntheticLaneSelection is not _SELECTION_RESULT_TYPE
        or any(
            vars(_LANE_TYPE).get(name) is not original
            for name, original in zip(
                _LANE_FIELDS + _LOOKUP_HOOKS,
                _ORIGINAL_LANE_DESCRIPTORS, strict=True,
            )
        )
        or any(
            vars(_SELECTION_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RESULT_FIELDS + _RESULT_DENIALS + _LOOKUP_HOOKS,
                _ORIGINAL_RESULT_DESCRIPTORS, strict=True,
            )
        )
    ):
        raise SyntheticLaneSelectionRejected(
            "work lane parser, codec or denial authority changed"
        )


def review_disconnected_work_lanes(
    lanes: tuple[SyntheticWorkLane, ...],
    *,
    completed: frozenset[str] = frozenset(),
    claimed_green: frozenset[str] = frozenset(),
    inflight_paths: tuple[str, ...] = (),
    protected_paths: tuple[str, ...] = (),
    max_selected: int = 4,
) -> SyntheticLaneSelection:
    """Propose isolated, free-only work; no caller claims become authority.

    Dependencies are complete only when independently confirmed *outside*
    this API. Passing a string in claimed_green is NOT CI attestation.
    protected_paths holds paths frozen or paused by the caller; it is not
    an authenticated policy source, but blocks overlapping proposed work.
    """
    _require_original_lane_selection_protocol()
    if (
        type(lanes) is not tuple or not 1 <= len(lanes) <= _MAX_LANES
        or type(completed) is not frozenset
        or type(claimed_green) is not frozenset
        or any(not _check_label(value) for value in completed | claimed_green)
        or not _check_labels(inflight_paths, paths=True)
        or not _check_labels(protected_paths, paths=True)
        or type(max_selected) is not int
        or not 1 <= max_selected <= _MAX_SELECTED
    ):
        raise SyntheticLaneSelectionRejected("invalid bounded work session")
    pinned = tuple((lane, tuple(getattr(lane, f.name) for f in fields(lane)))
                   for lane in lanes if type(lane) is SyntheticWorkLane)
    if len(pinned) != len(lanes):
        raise SyntheticLaneSelectionRejected("exact work-lane type required")

    def assert_epoch() -> None:
        _require_original_lane_selection_protocol()
        if len(lanes) != len(pinned) or any(
            current is not old_lane
            or any(getattr(current, f.name) is not old_value
                   for f, old_value in zip(fields(current), values, strict=True))
            for current, (old_lane, values) in zip(lanes, pinned, strict=True)
        ):
            raise SyntheticLaneSelectionRejected("work lanes changed during selection")

    assert_epoch()
    seen = set()
    for lane in lanes:
        if (
            not _check_label(lane.lane_id) or lane.lane_id in seen
            or type(lane.priority) is not int or not 0 <= lane.priority <= 1000
            or not _check_labels(lane.touches, paths=True) or not lane.touches
            or not _check_labels(lane.depends_on)
            or not _check_labels(lane.requires_green)
            or type(lane.cost_class) is not str or lane.cost_class not in _COSTS
            or type(lane.requires_approval) is not bool
            or type(lane.reversible) is not bool
            or lane.lane_id in lane.depends_on
        ):
            raise SyntheticLaneSelectionRejected("invalid work-lane contract")
        seen.add(lane.lane_id)
    by_name = {lane.lane_id: lane for lane in lanes}
    if not completed <= seen or any(
        dep not in seen for lane in lanes for dep in lane.depends_on
    ):
        raise SyntheticLaneSelectionRejected("unknown work dependency")
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise SyntheticLaneSelectionRejected("cyclic work dependencies")
        if name not in visited:
            visiting.add(name)
            for dep in by_name[name].depends_on:
                visit(dep)
            visiting.remove(name)
            visited.add(name)

    for lane in lanes:
        visit(lane.lane_id)
    assert_epoch()
    selected: list[SyntheticWorkLane] = []
    deferred: list[tuple[str, str]] = []
    for lane in sorted(lanes, key=lambda value: (-value.priority, value.lane_id)):
        assert_epoch()
        reason = None
        if lane.lane_id in completed:
            reason = "already_completed"
        elif any(
            _overlap(touch, protected)
            for touch in lane.touches for protected in protected_paths
        ):
            reason = "protected_path"
        elif lane.cost_class != "free_local":
            reason = "cost_unapproved"
        elif lane.requires_approval:
            reason = "explicit_approval_required"
        elif not lane.reversible:
            reason = "irreversible"
        elif not set(lane.depends_on) <= completed:
            reason = "dependencies_unfinished"
        elif not set(lane.requires_green) <= claimed_green:
            reason = "exact_head_green_unverified"
        elif any(_overlap(touch, busy) for touch in lane.touches for busy in inflight_paths):
            reason = "inflight_ci_conflict"
        elif any(
            _overlap(touch, other)
            for earlier in selected for touch in lane.touches for other in earlier.touches
        ):
            reason = "selected_lane_conflict"
        elif len(selected) >= max_selected:
            reason = "session_capacity"
        if reason:
            deferred.append((lane.lane_id, reason))
        else:
            selected.append(lane)
        assert_epoch()
    decision = (
        tuple(lane.lane_id for lane in selected), tuple(deferred),
    )
    encoded = json.dumps(decision, ensure_ascii=True, separators=(",", ":")).encode()
    assert_epoch()
    digest = "lanes_" + hashlib.sha256(_DOMAIN + encoded).hexdigest()
    assert_epoch()
    _require_original_lane_selection_protocol()
    result = SyntheticLaneSelection(decision[0], decision[1], digest)
    assert_epoch()
    def assert_result() -> None:
        assert_epoch()
        if (
            type(result) is not _SELECTION_RESULT_TYPE
            or result.selected is not decision[0]
            or result.deferred is not decision[1]
            or result.diagnostic_digest is not digest
        ):
            raise SyntheticLaneSelectionRejected("work decision changed during return")

    assert_result()
    # No selector diagnostic is permission for execution, writing to GitHub,
    # or incurring cost. Even False-returning descriptors may mutate inputs
    # or returned selections after the first field check.
    if (
        result.execution_authorized is not False
        or result.github_write_authorized is not False
        or result.spending_authorized is not False
    ):
        raise SyntheticLaneSelectionRejected("work decision forged authority")
    assert_result()
    _require_original_lane_selection_protocol()
    return result
