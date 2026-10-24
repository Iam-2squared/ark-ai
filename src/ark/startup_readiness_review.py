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


def _identifier(value: object, label: str) -> str:
    if type(value) is not str or not value.strip() or len(value) > 256:
        raise ValueError(f"{label} must be nonempty bounded exact text")
    return value


@dataclass(frozen=True, slots=True)
class StartupComponent:
    component_id: str
    dependencies: tuple[str, ...] = ()
    local_state: ReadinessState = ReadinessState.READY
    failure_code: str | None = None
    schema_revision: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.component_id, "component_id")
        if type(self.dependencies) is not tuple:
            raise TypeError("dependencies must be an exact tuple")
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
        if type(self.components) is not tuple or not self.components:
            raise ValueError("startup snapshot structure changed")
        names: list[str] = []
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
            names.append(item.component_id)
        if names != sorted(set(names)):
            raise ValueError("startup snapshot component order changed")

        # Internal validators and hash functions can be replaced by local
        # fixture callbacks. Hold each original carrier through those calls:
        # a mutation restored by the next callback must not go unnoticed.
        components_epoch = self.components
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
                or len(components_epoch) != len(carrier_epoch)
                or any(
                    item is not original
                    or item.component_id != old_id
                    or item.dependencies is not old_dependencies
                    or item.local_state is not old_local
                    or item.effective_state is not old_effective
                    or item.failure_code != old_failure
                    or item.schema_revision != old_schema
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
                return item.effective_state
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
        return tuple(sorted(found))


def evaluate_startup_readiness(
    probes: Iterable[StartupComponent],
) -> StartupSnapshot:
    """Evaluate an isolated probe snapshot without activating any capability."""
    # Bounded incremental hydration is necessary: tuple(probes) consumes a
    # caller-controlled iterable before we can pin an earlier yielded probe,
    # and an infinite generator would bypass the review budget altogether.
    snapshot_list: list[StartupComponent] = []
    source_epoch: list[tuple[object, ...]] = []

    def assert_source_epoch() -> None:
        if any(
            type(entry) is not StartupComponent
            or entry.component_id != component_id
            or entry.dependencies is not dependencies
            or entry.local_state is not local_state
            or entry.failure_code != failure_code
            or entry.schema_revision != schema_revision
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
        if len(snapshot_list) >= 10_000:
            raise ValueError("readiness graph exceeds local review budget")
        if type(entry) is not StartupComponent:
            raise TypeError("startup requires exact StartupComponent entries")
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
    components = tuple(
        ComponentResult(
            name,
            tuple(sorted(by_name[name].dependencies)),
            by_name[name].local_state,
            effective[name],
            by_name[name].failure_code,
            by_name[name].schema_revision,
        )
        for name in sorted(by_name)
    )
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
    return StartupSnapshot(components, "startup_" + hashlib.sha256(encoded).hexdigest())
