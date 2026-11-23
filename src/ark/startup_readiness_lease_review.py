"""Freshness and exact-component gate for disconnected startup probe snapshots.

Synthetic READY assertions are not proof of a functioning local machine,
trusted clock, human consent or ToolBackend safety. This reviewer cannot
grant real execution, notification or hardware access.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .startup_readiness_review import (
    ComponentResult,
    ReadinessState,
    StartupSnapshot,
    _assert_original_startup_constructors,
)

_MAX = 2**63 - 1
_LIMIT = 512
# These are safety limits, not caller-adjustable convenience settings.
_ORIGINAL_MAX = _MAX
_ORIGINAL_LIMIT = _LIMIT
_ORIGINAL_SOURCE_GUARD = _assert_original_startup_constructors
_ORIGINAL_UNICODEDATA = unicodedata
_ORIGINAL_UNICODE_CATEGORY = unicodedata.category


def _require_original_unicode_category() -> None:
    if (
        unicodedata is not _ORIGINAL_UNICODEDATA
        or unicodedata.category is not _ORIGINAL_UNICODE_CATEGORY
    ):
        raise SyntheticStartupLeaseRejected(
            "startup lease Unicode category classifier changed"
        )


class SyntheticStartupLeaseRejected(RuntimeError):
    """A disconnected readiness lease is missing, stale or inconsistent."""


@dataclass(frozen=True, slots=True)
class SyntheticReadinessRequirement:
    component_id: str
    schema_revision: str

    def assert_shape(self) -> None:
        _require_original_unicode_category()
        for label, value in (
            ("component", self.component_id),
            ("schema", self.schema_revision),
        ):
            if type(value) is not str or not value.strip() or len(value) > 256:
                raise SyntheticStartupLeaseRejected(
                    f"invalid exact {label} requirement"
                )
            # Match StartupComponent's UTF-8 byte budget. A reflectively
            # altered frozen requirement must not become a fresh READY claim
            # merely because its code-point count is under the limit.
            try:
                byte_count = len(value.encode("utf-8", errors="strict"))
            except UnicodeEncodeError as exc:
                raise SyntheticStartupLeaseRejected(
                    f"invalid UTF-8 {label} requirement"
                ) from exc
            # NUL is not a valid component or schema identity even though
            # it fits the UTF-8 byte budget. Refuse before reading any
            # readiness snapshot or matching a required component.
            if "\x00" in value:
                raise SyntheticStartupLeaseRejected(
                    f"invalid NUL {label} requirement"
                )
            # Match StartupComponent identity admission: requirement values
            # must not inject terminal controls or visually redirect diagnostics.
            # Refuse these before reading any readiness snapshot or matching a
            # required component. This remains a disconnected fixture boundary.
            if any(ord(character) < 32 or ord(character) == 127 for character in value):
                raise SyntheticStartupLeaseRejected(
                    f"invalid ASCII control {label} requirement"
                )
            if any(
                _ORIGINAL_UNICODE_CATEGORY(chr(point)) == "Cf"
                or 0x80 <= point <= 0x9F
                or point in (0x00AD, 0x034F, 0x061C, 0x180E, 0x200E, 0x200F)
                or 0x200B <= point <= 0x200D
                or 0x202A <= point <= 0x202E
                or 0x2060 <= point <= 0x206F
                or point in (0x2028, 0x2029, 0xFEFF)
                for point in map(ord, value)
            ):
                raise SyntheticStartupLeaseRejected(
                    f"invalid Unicode formatting control {label} requirement"
                )
            _require_original_unicode_category()
            if byte_count > 256:
                raise SyntheticStartupLeaseRejected(
                    f"invalid UTF-8 {label} requirement byte budget"
                )


@dataclass(frozen=True, slots=True)
class SyntheticStartupLeaseReview:
    snapshot_digest: str
    required_components: tuple[str, ...]
    captured_at_ms: int
    checked_at_ms: int

    @property
    def startup_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False



# Capture import-original fixture carrier identities. Frozen instance fields
# can still be replaced with executable class descriptors, so validating an
# exact instance alone does not protect the first private probe-field read.
_REQUIREMENT_TYPE = SyntheticReadinessRequirement
_REQUIREMENT_FIELDS = ("component_id", "schema_revision")
_REQUIREMENT_HOOKS = (
    "__init__", "__new__", "__getattribute__", "__getattr__", "assert_shape",
)
_ORIGINAL_REQUIREMENT_FIELDS = tuple(
    vars(_REQUIREMENT_TYPE)[name] for name in _REQUIREMENT_FIELDS
)
_ORIGINAL_REQUIREMENT_HOOKS = tuple(
    vars(_REQUIREMENT_TYPE).get(name) for name in _REQUIREMENT_HOOKS
)

_LEASE_TYPE = SyntheticStartupLeaseReview
_LEASE_FIELDS = (
    "snapshot_digest", "required_components", "captured_at_ms", "checked_at_ms",
)
_LEASE_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_LEASE_FIELDS = tuple(
    vars(_LEASE_TYPE)[name] for name in _LEASE_FIELDS
)
_ORIGINAL_LEASE_HOOKS = tuple(
    vars(_LEASE_TYPE).get(name) for name in _LEASE_HOOKS
)

_LEASE_AUTHORITY_FIELDS = (
    "startup_authorized", "dispatch_authorized", "notification_authorized",
)
_ORIGINAL_LEASE_AUTHORITY = tuple(
    vars(_LEASE_TYPE)[name] for name in _LEASE_AUTHORITY_FIELDS
)

# The descriptor inventories and the tuples holding their import-original
# carriers are themselves safety inputs. Pin both layers before using zip()
# so an empty/equal-valued replacement cannot silently skip every check.
_ORIGINAL_GUARD_VECTOR_REFERENCES = (
    _REQUIREMENT_FIELDS,
    _REQUIREMENT_HOOKS,
    _LEASE_FIELDS,
    _LEASE_HOOKS,
    _LEASE_AUTHORITY_FIELDS,
    _ORIGINAL_REQUIREMENT_FIELDS,
    _ORIGINAL_REQUIREMENT_HOOKS,
    _ORIGINAL_LEASE_FIELDS,
    _ORIGINAL_LEASE_HOOKS,
    _ORIGINAL_LEASE_AUTHORITY,
)


def _require_original_requirement() -> None:
    if (
        SyntheticReadinessRequirement is not _REQUIREMENT_TYPE
        or any(
            vars(_REQUIREMENT_TYPE).get(name) is not original
            for names, originals in (
                (_REQUIREMENT_FIELDS, _ORIGINAL_REQUIREMENT_FIELDS),
                (_REQUIREMENT_HOOKS, _ORIGINAL_REQUIREMENT_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticStartupLeaseRejected(
            "readiness requirement descriptor changed before review"
        )


def _require_original_lease_result() -> None:
    if (
        SyntheticStartupLeaseReview is not _LEASE_TYPE
        or any(
            vars(_LEASE_TYPE).get(name) is not original
            for names, originals in (
                (_LEASE_FIELDS, _ORIGINAL_LEASE_FIELDS),
                (_LEASE_HOOKS, _ORIGINAL_LEASE_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticStartupLeaseRejected(
            "readiness result constructor or descriptor changed"
        )
    # A substituted False-returning property can execute arbitrary code
    # before a receipt is returned. Pin denial descriptors at import and
    # reject them before accessing even synthetic private probe metadata.
    if any(
        vars(_LEASE_TYPE).get(name) is not original
        for name, original in zip(
            _LEASE_AUTHORITY_FIELDS, _ORIGINAL_LEASE_AUTHORITY, strict=True,
        )
    ):
        raise SyntheticStartupLeaseRejected(
            "readiness result authority epoch changed before review"
        )


def _require_original_lease_protocol(
    _original_guard_vector_references: tuple[object, ...] = _ORIGINAL_GUARD_VECTOR_REFERENCES,
) -> None:
    # The carrier tuple is itself a module-level safety input. Capture its
    # import-original identity in this function's default arguments and reject
    # an empty/equal-valued rebind before reading any snapshot or requirement.
    if _ORIGINAL_GUARD_VECTOR_REFERENCES is not _original_guard_vector_references:
        raise SyntheticStartupLeaseRejected(
            "startup lease guard-vector reference changed"
        )
    # Pin descriptor-name vectors and the tuples that carry their original
    # class descriptors before any snapshot, requirement or result access.
    # Otherwise an empty/equal-valued replacement can make zip() skip checks.
    current_vectors = (
        _REQUIREMENT_FIELDS,
        _REQUIREMENT_HOOKS,
        _LEASE_FIELDS,
        _LEASE_HOOKS,
        _LEASE_AUTHORITY_FIELDS,
        _ORIGINAL_REQUIREMENT_FIELDS,
        _ORIGINAL_REQUIREMENT_HOOKS,
        _ORIGINAL_LEASE_FIELDS,
        _ORIGINAL_LEASE_HOOKS,
        _ORIGINAL_LEASE_AUTHORITY,
    )
    if any(
        current is not original
        for current, original in zip(
            current_vectors, _original_guard_vector_references, strict=True,
        )
    ):
        raise SyntheticStartupLeaseRejected("startup lease guard vector changed")
    # A forged snapshot/ComponentResult slot can execute before integrity
    # checks unless the source's original class descriptors are pinned.
    if (
        type(_MAX) is not int or _MAX != _ORIGINAL_MAX
        or type(_LIMIT) is not int or _LIMIT != _ORIGINAL_LIMIT
        or _assert_original_startup_constructors is not _ORIGINAL_SOURCE_GUARD
    ):
        raise SyntheticStartupLeaseRejected("startup lease limits or source guard changed")
    try:
        _assert_original_startup_constructors()
    except (TypeError, ValueError, AttributeError) as exc:
        raise SyntheticStartupLeaseRejected(
            "startup lease source descriptor changed"
        ) from exc


# Capture the import-original guard helpers as part of the lease protocol.
# Rebinding a helper to a no-op could otherwise make an empty descriptor
# vector skip the checks that protect requirement/result carriers.
_ORIGINAL_LEASE_GUARD_HELPERS = (
    _require_original_requirement,
    _require_original_lease_result,
    _require_original_lease_protocol,
)


def review_synthetic_startup_lease(
    snapshot: StartupSnapshot,
    requirements: tuple[SyntheticReadinessRequirement, ...],
    *,
    captured_at_ms: int,
    now_ms: int,
    max_age_ms: int,
    _original_lease_guard_helpers: tuple[object, ...] = _ORIGINAL_LEASE_GUARD_HELPERS,
) -> SyntheticStartupLeaseReview:
    """Check current fixture state against a bounded exact dependency contract.

    Caller-supplied clocks and probe values are untrusted. The lease can
    become stale or blocked after review; it is not a capability grant.
    """
    def assert_original_lease_helpers() -> None:
        current_helpers = (
            _require_original_requirement,
            _require_original_lease_result,
            _require_original_lease_protocol,
        )
        if (
            _ORIGINAL_LEASE_GUARD_HELPERS is not _original_lease_guard_helpers
            or any(
                current is not original
                for current, original in zip(
                    current_helpers, _original_lease_guard_helpers, strict=True,
                )
            )
        ):
            raise SyntheticStartupLeaseRejected(
                "startup lease helper identity changed"
            )
        _original_lease_guard_helpers[2]()

    assert_original_lease_helpers()
    if (
        type(snapshot) is not StartupSnapshot
        or type(requirements) is not tuple
        or not 1 <= len(requirements) <= _LIMIT
        or any(type(item) is not SyntheticReadinessRequirement for item in requirements)
        or any(type(value) is not int for value in (
            captured_at_ms, now_ms, max_age_ms,
        ))
    ):
        raise SyntheticStartupLeaseRejected("exact synthetic lease inputs required")
    if (
        not 0 <= captured_at_ms <= now_ms <= _MAX
        or not 0 <= max_age_ms <= _MAX
        or now_ms - captured_at_ms > max_age_ms
    ):
        raise SyntheticStartupLeaseRejected("synthetic startup lease expired or clock regressed")
    # Require import-original descriptors before reading any requirement
    # field or invoking a caller-replaceable shape validator.
    _require_original_requirement()
    _require_original_lease_result()
    # Snapshot the ORIGINAL requirement carriers before the first reentrant
    # shape method; a later callback must not promote a substitute component.
    epoch = tuple((item, item.component_id, item.schema_revision) for item in requirements)

    def assert_requirements() -> None:
        assert_original_lease_helpers()
        _require_original_requirement()
        try:
            stable = len(requirements) == len(epoch) and all(
                current is item
                and current.component_id is component_id
                and current.schema_revision is schema_revision
                for current, (item, component_id, schema_revision) in zip(
                    requirements, epoch, strict=True,
                )
            )
        except (AttributeError, TypeError, ValueError):
            stable = False
        if not stable:
            raise SyntheticStartupLeaseRejected(
                "readiness requirement epoch changed during review"
            )

    for item in requirements:
        _require_original_requirement()
        item.assert_shape()
        assert_requirements()
    names = tuple(item.component_id for item in requirements)
    if len(set(names)) != len(names):
        raise SyntheticStartupLeaseRejected("duplicate required readiness component")
    # The snapshot digest binds values, not the identity of the component
    # carriers. An integrity callback may replace the entire tuple, or an
    # equal-valued ComponentResult, after validation and before admission.
    # Pin both original carriers and values before the first callback.
    components = snapshot.components
    if type(components) is not tuple or any(
        type(item) is not ComponentResult for item in components
    ):
        raise SyntheticStartupLeaseRejected("startup snapshot components changed")
    digest = snapshot.digest
    component_epoch = tuple((
        item, item.component_id, item.dependencies, item.local_state,
        item.effective_state, item.failure_code, item.schema_revision,
    ) for item in components)

    def assert_epoch() -> None:
        assert_original_lease_helpers()
        _require_original_lease_result()
        if (
            snapshot.components is not components
            or snapshot.digest is not digest
            or len(snapshot.components) != len(component_epoch)
            or any(
                current is not original
                or current.dependencies is not dependencies
                or any(
                    now is not original
                    for now, original in zip(
                        (current.component_id, current.dependencies,
                         current.local_state, current.effective_state,
                         current.failure_code, current.schema_revision),
                        (component_id, dependencies, local, effective, failure, schema),
                        strict=True,
                    )
                )
                for current, (
                    original, component_id, dependencies, local, effective,
                    failure, schema,
                ) in zip(snapshot.components, component_epoch, strict=True)
            )
        ):
            raise SyntheticStartupLeaseRejected(
                "readiness inputs changed during review"
            )

    try:
        snapshot._assert_integrity()
        assert_epoch()
        by_name = {entry.component_id: entry for entry in components}
        # Check the copied admission contract, never a requirement object
        # that a reentrant integrity callback can temporarily redirect to
        # a different READY component and later restore.
        for _carrier, component_id, schema_revision in epoch:
            current = by_name.get(component_id)
            if current is None:
                raise SyntheticStartupLeaseRejected("required component is not present")
            if (
                current.effective_state is not ReadinessState.READY
                or current.local_state is not ReadinessState.READY
                or current.schema_revision != schema_revision
            ):
                raise SyntheticStartupLeaseRejected(
                    "required component blocked, degraded or schema-stale"
                )
        # Preserve the required-component denial diagnostic for a blocked
        # original dependency. A different but READY temporary requirement
        # must still fail before the next callback can restore it.
        if any(
            type(item) is not SyntheticReadinessRequirement
            or item.component_id != component_id
            or item.schema_revision != schema_revision
            for item, component_id, schema_revision in epoch
        ):
            raise SyntheticStartupLeaseRejected(
                "readiness inputs changed during review"
            )
        snapshot._assert_integrity()
        assert_epoch()
        assert_requirements()
        if (
            snapshot.digest != digest
            or any(
                type(item) is not SyntheticReadinessRequirement
                or item.component_id != component_id
                or item.schema_revision != revision
                for item, component_id, revision in epoch
            )
        ):
            raise SyntheticStartupLeaseRejected("readiness inputs changed during review")
    except (ValueError, TypeError, AttributeError) as exc:
        raise SyntheticStartupLeaseRejected("startup snapshot integrity rejected") from exc
    assert_requirements()
    _require_original_lease_result()
    result = SyntheticStartupLeaseReview(
        digest, tuple(sorted(names)), captured_at_ms, now_ms,
    )
    assert_epoch()
    assert_requirements()
    if (
        type(result) is not SyntheticStartupLeaseReview
        or result.snapshot_digest is not digest
        or result.required_components != tuple(sorted(names))
        or result.captured_at_ms is not captured_at_ms
        or result.checked_at_ms is not now_ms
    ):
        raise SyntheticStartupLeaseRejected(
            "readiness result changed during construction"
        )

    # A readiness receipt is diagnostic, never permission to start a backend.
    # Check every denial property before return; property callbacks may still
    # reflectively retarget the frozen result, required probes or source graph.
    # A post-constructor check alone cannot detect a False-returning getter
    # that changes these inputs after its first inspection.
    receipt_epoch = (
        result.snapshot_digest, result.required_components,
        result.captured_at_ms, result.checked_at_ms,
    )

    def assert_result_epoch() -> None:
        assert_original_lease_helpers()
        _require_original_lease_result()
        if (
            type(result) is not SyntheticStartupLeaseReview
            or any(current is not previous for current, previous in zip(
                (
                    result.snapshot_digest, result.required_components,
                    result.captured_at_ms, result.checked_at_ms,
                ),
                receipt_epoch, strict=True,
            ))
        ):
            raise SyntheticStartupLeaseRejected("readiness receipt epoch changed")

    for flag in (
        "startup_authorized", "dispatch_authorized", "notification_authorized",
    ):
        if getattr(result, flag) is not False:
            raise SyntheticStartupLeaseRejected("readiness receipt gained authority")
        assert_result_epoch()
        assert_epoch()
        assert_requirements()

    # The last integrity callback also executes Python code; close all epochs
    # after it, without confusing a READY probe with actual startup authority.
    snapshot._assert_integrity()
    assert_epoch()
    assert_requirements()
    assert_result_epoch()
    return result
