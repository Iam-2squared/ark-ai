"""Disconnected deterministic startup readiness for synthetic local probes.

This evaluator neither opens real stores nor certifies that a backend, person,
credential, or system clock is trustworthy. A READY value is only a supplied
probe assertion until a separately reviewed integration supplies its evidence.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from heapq import heappop, heappush


class ReadinessState(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    DEPENDENCY_BLOCKED = "dependency_blocked"


_MAX_COMPONENTS = 10_000
_MAX_DEPENDENCIES_PER_COMPONENT = 4_096
_MAX_DEPENDENCY_EDGES = 65_536
# These are import-time admission limits. A replaced module global must not
# expand a caller-controlled graph or allow a cached oversized READY witness.
_ORIGINAL_READINESS_BUDGETS = (
    _MAX_COMPONENTS, _MAX_DEPENDENCIES_PER_COMPONENT, _MAX_DEPENDENCY_EDGES,
)


def _require_original_readiness_budgets() -> None:
    observed = (
        _MAX_COMPONENTS, _MAX_DEPENDENCIES_PER_COMPONENT, _MAX_DEPENDENCY_EDGES,
    )
    if (
        any(type(limit) is not int for limit in observed)
        or observed != _ORIGINAL_READINESS_BUDGETS
    ):
        raise ValueError("readiness admission budgets changed")


_ORIGINAL_READINESS_BUDGET_CHECK = _require_original_readiness_budgets


def _identifier(value: object, label: str) -> str:
    """Enforce a strict UTF-8 byte budget for disconnected probe identities.

    The cheap character cap precedes encoding to bound allocations. This
    stricter foundation input rule does not modify any frozen V1/V2 schema.
    """
    if type(value) is not str or not value.strip() or len(value) > 256:
        raise ValueError(f"{label} must be nonempty bounded exact text")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise ValueError(f"{label} must be valid UTF-8 exact text") from exc
    if size > 256:
        raise ValueError(f"{label} exceeds 256 UTF-8 bytes")
    return value


@dataclass(frozen=True, slots=True)
class StartupComponent:
    component_id: str
    dependencies: tuple[str, ...] = ()
    local_state: ReadinessState = ReadinessState.READY
    failure_code: str | None = None
    schema_revision: str | None = None

    def __post_init__(self) -> None:
        # A slotted field can be replaced with executable descriptor code.
        # Validate the original class before reading even the first label.
        _assert_original_startup_constructors()
        _identifier(self.component_id, "component_id")
        if type(self.dependencies) is not tuple:
            raise TypeError("dependencies must be an exact tuple")
        if len(self.dependencies) > _MAX_DEPENDENCIES_PER_COMPONENT:
            raise ValueError("readiness per-component dependency budget exceeded")
        for dependency in self.dependencies:
            _identifier(dependency, "dependency")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("duplicate readiness dependency")
        if self.component_id in self.dependencies:
            raise ValueError("readiness component cannot depend on itself")
        if type(self.local_state) is not ReadinessState:
            raise TypeError("local_state must be an exact ReadinessState")
        if self.local_state is ReadinessState.DEPENDENCY_BLOCKED:
            raise ValueError("dependency-blocked cannot be supplied as local state")
        if self.failure_code is not None:
            _identifier(self.failure_code, "failure_code")
        if self.schema_revision is not None:
            _identifier(self.schema_revision, "schema_revision")


@dataclass(frozen=True, slots=True)
class ComponentResult:
    component_id: str
    dependencies: tuple[str, ...]
    local_state: ReadinessState
    effective_state: ReadinessState
    failure_code: str | None
    schema_revision: str | None


@dataclass(frozen=True, slots=True)
class StartupSnapshot:
    """Content-minimized immutable epoch of one disconnected readiness graph."""

    components: tuple[ComponentResult, ...]
    digest: str

    def _assert_integrity(self) -> None:
        """Refuse reflected mutation of a previously evaluated snapshot.

        A local checksum detects stale or altered cached diagnostics; it is
        neither external attestation nor permission to activate a capability.
        """
        _assert_original_startup_constructors()
        if (
            type(self.components) is not tuple or not self.components
            or len(self.components) > _MAX_COMPONENTS
        ):
            raise ValueError("startup snapshot structure changed")
        names: list[str] = []
        edge_count = 0
        for item in self.components:
            if (
                type(item) is not ComponentResult
                or type(item.local_state) is not ReadinessState
                or type(item.effective_state) is not ReadinessState
                or type(item.dependencies) is not tuple
                or any(type(parent) is not str for parent in item.dependencies)
                or item.dependencies != tuple(sorted(set(item.dependencies)))
                or type(item.component_id) is not str
                or (item.failure_code is not None and type(item.failure_code) is not str)
                or (item.schema_revision is not None and type(item.schema_revision) is not str)
            ):
                raise ValueError("startup snapshot component changed")
            if len(item.dependencies) > _MAX_DEPENDENCIES_PER_COMPONENT:
                raise ValueError("startup snapshot dependency budget exceeded")
            edge_count += len(item.dependencies)
            if edge_count > _MAX_DEPENDENCY_EDGES:
                raise ValueError("startup snapshot dependency budget exceeded")
            names.append(item.component_id)
        if names != sorted(set(names)):
            raise ValueError("startup snapshot component order changed")

        # Internal validators and hash functions can be replaced by local
        # fixture callbacks. Hold each original carrier through those calls:
        # a mutation restored by the next callback must not go unnoticed.
        components_epoch = self.components
        digest_epoch = self.digest
        carrier_epoch = tuple(
            (
                item, item.component_id, item.dependencies, item.local_state,
                item.effective_state, item.failure_code, item.schema_revision,
            )
            for item in components_epoch
        )

        def assert_component_epoch() -> None:
            if (
                self.components is not components_epoch
                or self.digest is not digest_epoch
                or len(components_epoch) != len(carrier_epoch)
                or any(
                    item is not original
                    or item.component_id is not old_id
                    or item.dependencies is not old_dependencies
                    or item.local_state is not old_local
                    or item.effective_state is not old_effective
                    or item.failure_code is not old_failure
                    or item.schema_revision is not old_schema
                    for item, (
                        original, old_id, old_dependencies, old_local,
                        old_effective, old_failure, old_schema,
                    ) in zip(components_epoch, carrier_epoch, strict=True)
                )
            ):
                raise ValueError("startup snapshot changed during integrity review")

        # A digest is not sufficient: it can be recomputed over a logically
        # contradictory snapshot. Re-derive graph semantics before returning a
        # cached READY/BLOCKED diagnosis. This is still local, not attestation.
        by_name = {item.component_id: item for item in self.components}
        following: dict[str, list[str]] = {name: [] for name in by_name}
        indegree = {name: len(item.dependencies) for name, item in by_name.items()}
        for item in self.components:
            try:
                _identifier(item.component_id, "component_id")
                assert_component_epoch()
                for parent in item.dependencies:
                    _identifier(parent, "dependency")
                    assert_component_epoch()
                if item.failure_code is not None:
                    _identifier(item.failure_code, "failure_code")
                    assert_component_epoch()
                if item.schema_revision is not None:
                    _identifier(item.schema_revision, "schema_revision")
                    assert_component_epoch()
            except ValueError as exc:
                raise ValueError("startup snapshot identifier changed") from exc
            if item.local_state is ReadinessState.DEPENDENCY_BLOCKED:
                raise ValueError("startup snapshot local state changed")
            for parent in item.dependencies:
                if parent == item.component_id or parent not in by_name:
                    raise ValueError("startup snapshot dependency changed")
                following[parent].append(item.component_id)

        pending: list[str] = []
        for name, degree in indegree.items():
            if degree == 0:
                heappush(pending, name)
        resolved: dict[str, ReadinessState] = {}
        while pending:
            name = heappop(pending)
            item = by_name[name]
            if item.local_state is ReadinessState.BLOCKED:
                derived = ReadinessState.BLOCKED
            elif any(
                resolved[parent] in (
                    ReadinessState.BLOCKED, ReadinessState.DEPENDENCY_BLOCKED
                )
                for parent in item.dependencies
            ):
                derived = ReadinessState.DEPENDENCY_BLOCKED
            else:
                derived = item.local_state
            if derived is not item.effective_state:
                raise ValueError("startup snapshot effective state changed")
            resolved[name] = derived
            for child in following[name]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    heappush(pending, child)
        if len(resolved) != len(by_name):
            raise ValueError("startup snapshot dependency cycle")
        payload = {
            "schema_version": 1,
            "components": [
                {
                    "id": item.component_id,
                    "dependencies": item.dependencies,
                    "local": item.local_state.value,
                    "effective": item.effective_state.value,
                    "failure_code": item.failure_code,
                    "schema_revision": item.schema_revision,
                }
                for item in self.components
            ],
        }
        assert_component_epoch()
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        assert_component_epoch()
        expected = "startup_" + hashlib.sha256(encoded).hexdigest()
        assert_component_epoch()
        if type(self.digest) is not str or self.digest != expected:
            raise ValueError("startup snapshot witness changed")

    def state(self, component_id: str) -> ReadinessState:
        self._assert_integrity()
        # Caller-id validation is a reentrant boundary. Recheck the retained
        # graph after it, before returning READY or calculating blockers.
        _identifier(component_id, "component_id")
        self._assert_integrity()
        for item in self.components:
            if item.component_id == component_id:
                observed = item.effective_state
                # Even a getter returning a valid READY/BLOCKED enum can
                # reflectively mutate the rest of the frozen cached graph.
                # Recompute integrity after that final lookup before reuse.
                self._assert_integrity()
                if (
                    type(observed) is not ReadinessState
                    or item.effective_state is not observed
                ):
                    raise ValueError("startup snapshot changed at state return")
                return observed
        self._assert_integrity()
        raise KeyError(f"unknown readiness component: {component_id}")

    def root_blockers(self, component_id: str) -> tuple[str, ...]:
        """Return local BLOCKED ancestors, not a new readiness decision."""
        self._assert_integrity()
        # Caller-id validation is a reentrant boundary. Recheck the retained
        # graph after it, before returning READY or calculating blockers.
        _identifier(component_id, "component_id")
        self._assert_integrity()
        by_name = {item.component_id: item for item in self.components}
        if component_id not in by_name:
            raise KeyError(f"unknown readiness component: {component_id}")
        found: set[str] = set()
        visited: set[str] = set()
        pending = [component_id]
        while pending:
            name = pending.pop()
            if name in visited:
                continue
            visited.add(name)
            item = by_name[name]
            if item.local_state is ReadinessState.BLOCKED:
                found.add(name)
            else:
                pending.extend(item.dependencies)
        blockers = tuple(sorted(found))
        # Traversal itself reads caller-reflectable fields. A previously
        # validated graph can change after the pre-traversal digest check.
        self._assert_integrity()
        return blockers


# Validation/receipt construction is executable Python, even for frozen slots.
# Bind the original constructors before any caller-controlled iterator or hash
# callback is allowed to replace them with a forged READY-producing function.
_STARTUP_COMPONENT_TYPE = StartupComponent
_COMPONENT_RESULT_TYPE = ComponentResult
_STARTUP_SNAPSHOT_RESULT_TYPE = StartupSnapshot
_ORIGINAL_COMPONENT_INIT = vars(_STARTUP_COMPONENT_TYPE)["__init__"]
_ORIGINAL_COMPONENT_POST_INIT = vars(_STARTUP_COMPONENT_TYPE)["__post_init__"]
_ORIGINAL_COMPONENT_RESULT_INIT = vars(_COMPONENT_RESULT_TYPE)["__init__"]
_ORIGINAL_SNAPSHOT_INIT = vars(_STARTUP_SNAPSHOT_RESULT_TYPE)["__init__"]
# Check exact original data slots/lookup hooks in addition to constructors.
# A frozen dataclass does not prevent a malicious property or overridden
# __getattribute__ from accessing probe identities before validation.
_STARTUP_CARRIER_TYPES = (
    _STARTUP_COMPONENT_TYPE, _COMPONENT_RESULT_TYPE,
    _STARTUP_SNAPSHOT_RESULT_TYPE,
)
_STARTUP_CARRIER_FIELDS = (
    ("component_id", "dependencies", "local_state", "failure_code", "schema_revision"),
    (
        "component_id", "dependencies", "local_state", "effective_state",
        "failure_code", "schema_revision",
    ),
    ("components", "digest"),
)
_STARTUP_CARRIER_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_CARRIER_FIELDS = tuple(
    tuple(vars(kind)[field] for field in fields)
    for kind, fields in zip(
        _STARTUP_CARRIER_TYPES, _STARTUP_CARRIER_FIELDS, strict=True,
    )
)
_ORIGINAL_CARRIER_HOOKS = tuple(
    tuple(vars(kind).get(name) for name in _STARTUP_CARRIER_HOOKS)
    for kind in _STARTUP_CARRIER_TYPES
)


def _assert_original_startup_constructors() -> None:
    # Perform constant and verifier custody checks before inspecting a
    # reflectively mutable probe, cached snapshot, or caller generator.
    if _require_original_readiness_budgets is not _ORIGINAL_READINESS_BUDGET_CHECK:
        raise ValueError("readiness admission budgets changed")
    _ORIGINAL_READINESS_BUDGET_CHECK()
    if (
        StartupComponent is not _STARTUP_COMPONENT_TYPE
        or ComponentResult is not _COMPONENT_RESULT_TYPE
        or StartupSnapshot is not _STARTUP_SNAPSHOT_RESULT_TYPE
        or vars(_STARTUP_COMPONENT_TYPE).get("__init__") is not _ORIGINAL_COMPONENT_INIT
        or vars(_STARTUP_COMPONENT_TYPE).get("__post_init__")
        is not _ORIGINAL_COMPONENT_POST_INIT
        or vars(_COMPONENT_RESULT_TYPE).get("__init__")
        is not _ORIGINAL_COMPONENT_RESULT_INIT
        or vars(_STARTUP_SNAPSHOT_RESULT_TYPE).get("__init__")
        is not _ORIGINAL_SNAPSHOT_INIT
        or any(
            any(
                vars(kind).get(name) is not original
                for name, original in zip(fields, originals, strict=True)
            )
            for kind, fields, originals in zip(
                _STARTUP_CARRIER_TYPES, _STARTUP_CARRIER_FIELDS,
                _ORIGINAL_CARRIER_FIELDS, strict=True,
            )
        )
        or any(
            any(
                vars(kind).get(name) is not original
                for name, original in zip(
                    _STARTUP_CARRIER_HOOKS, originals, strict=True,
                )
            )
            for kind, originals in zip(
                _STARTUP_CARRIER_TYPES, _ORIGINAL_CARRIER_HOOKS, strict=True,
            )
        )
    ):
        raise ValueError("startup constructor authority changed")


def evaluate_startup_readiness(
    probes: Iterable[StartupComponent],
) -> StartupSnapshot:
    """Evaluate an isolated probe snapshot without activating any capability."""
    # Bounded incremental hydration is necessary: tuple(probes) consumes a
    # caller-controlled iterable before we can pin an earlier yielded probe,
    # and an infinite generator would bypass the review budget altogether.
    _assert_original_startup_constructors()
    snapshot_list: list[StartupComponent] = []
    source_epoch: list[tuple[object, ...]] = []
    edge_count = 0

    def assert_source_epoch() -> None:
        _assert_original_startup_constructors()
        if any(
            type(entry) is not StartupComponent
            or entry.component_id is not component_id
            or entry.dependencies is not dependencies
            or entry.local_state is not local_state
            or entry.failure_code is not failure_code
            or entry.schema_revision is not schema_revision
            for (
                entry, component_id, dependencies, local_state,
                failure_code, schema_revision,
            ) in source_epoch
        ):
            raise ValueError("startup input changed during readiness evaluation")

    for entry in probes:
        # The iterator's next() may have just mutated a previously yielded
        # object. Check before accepting this later component.
        assert_source_epoch()
        if len(snapshot_list) >= _MAX_COMPONENTS:
            raise ValueError("readiness graph exceeds local review budget")
        if type(entry) is not StartupComponent:
            raise TypeError("startup requires exact StartupComponent entries")
        edge_count += len(entry.dependencies)
        if edge_count > _MAX_DEPENDENCY_EDGES:
            raise ValueError("readiness graph dependency budget exceeded")
        source_epoch.append((
            entry, entry.component_id, entry.dependencies, entry.local_state,
            entry.failure_code, entry.schema_revision,
        ))
        snapshot_list.append(entry)
        assert_source_epoch()
    # StopIteration itself may execute caller code, too.
    assert_source_epoch()
    snapshot = tuple(snapshot_list)
    if not snapshot:
        raise ValueError("readiness graph must contain at least one component")

    by_name: dict[str, StartupComponent] = {}
    for entry in snapshot:
        _assert_original_startup_constructors()
        checked = StartupComponent(
            entry.component_id,
            entry.dependencies,
            entry.local_state,
            entry.failure_code,
            entry.schema_revision,
        )
        assert_source_epoch()
        if entry.component_id in by_name:
            raise ValueError("duplicate readiness component ID")
        by_name[entry.component_id] = checked

    followers: dict[str, list[str]] = {name: [] for name in by_name}
    indegree = {name: len(entry.dependencies) for name, entry in by_name.items()}
    for name, entry in by_name.items():
        for parent in entry.dependencies:
            if parent not in by_name:
                raise ValueError(f"unknown readiness dependency: {parent}")
            followers[parent].append(name)
    pending: list[str] = []
    for name, degree in indegree.items():
        if degree == 0:
            heappush(pending, name)
    effective: dict[str, ReadinessState] = {}
    while pending:
        name = heappop(pending)
        entry = by_name[name]
        if entry.local_state is ReadinessState.BLOCKED:
            state = ReadinessState.BLOCKED
        elif any(
            effective[parent] in (ReadinessState.BLOCKED, ReadinessState.DEPENDENCY_BLOCKED)
            for parent in entry.dependencies
        ):
            state = ReadinessState.DEPENDENCY_BLOCKED
        else:
            state = entry.local_state
        effective[name] = state
        for child in followers[name]:
            indegree[child] -= 1
            if indegree[child] == 0:
                heappush(pending, child)
    if len(effective) != len(by_name):
        raise ValueError("readiness dependency graph contains a cycle")

    assert_source_epoch()
    prepared_components = []
    for name in sorted(by_name):
        _assert_original_startup_constructors()
        prepared_components.append(ComponentResult(
            name,
            tuple(sorted(by_name[name].dependencies)),
            by_name[name].local_state,
            effective[name],
            by_name[name].failure_code,
            by_name[name].schema_revision,
        ))
        assert_source_epoch()
    components = tuple(prepared_components)
    payload = {
        "schema_version": 1,
        "components": [
            {
                "id": item.component_id,
                "dependencies": item.dependencies,
                "local": item.local_state.value,
                "effective": item.effective_state.value,
                "failure_code": item.failure_code,
                "schema_revision": item.schema_revision,
            }
            for item in components
        ],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert_source_epoch()
    # SHA-256 is another reentrant fixture boundary: do not return READY
    # evidence if a hash callback rewrites an earlier probe carrier.
    digest = "startup_" + hashlib.sha256(encoded).hexdigest()
    assert_source_epoch()
    # The result constructor itself can be an injected callback. Hold the
    # original probe epoch AND the computed ComponentResult carrier epoch
    # across it; a locally forged READY value must never leave this review.
    component_epoch = tuple((
        item, item.component_id, item.dependencies, item.local_state,
        item.effective_state, item.failure_code, item.schema_revision,
    ) for item in components)
    _assert_original_startup_constructors()
    result = StartupSnapshot(components, digest)
    _assert_original_startup_constructors()
    assert_source_epoch()
    if (
        type(result) is not _STARTUP_SNAPSHOT_RESULT_TYPE
        or result.components is not components
        or result.digest is not digest
        or any(
            type(item) is not ComponentResult
            or item is not original
            or item.component_id is not name
            or item.dependencies is not dependencies
            or item.local_state is not local_state
            or item.effective_state is not effective_state
            or item.failure_code is not failure_code
            or item.schema_revision is not schema_revision
            for item, (
                original, name, dependencies, local_state, effective_state,
                failure_code, schema_revision,
            ) in zip(components, component_epoch, strict=True)
        )
    ):
        raise ValueError("startup result changed during construction")
    return result
