"""Synthetic startup leases remain inert with poisoned requirement/result classes.

There is no real health probe, trusted time or authority to start a backend.
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest

import ark.startup_readiness_lease_review as lease
from ark.startup_readiness_review import StartupComponent, evaluate_startup_readiness

_MISSING = object()


def _fixture():
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-1"),
        StartupComponent("planner", ("memory",), schema_revision="planner-1"),
    ))
    requirements = (
        lease.SyntheticReadinessRequirement("memory", "memory-1"),
        lease.SyntheticReadinessRequirement("planner", "planner-1"),
    )
    return snapshot, requirements


def _review(state):
    snapshot, requirements = state
    return lease.review_synthetic_startup_lease(
        snapshot, requirements,
        captured_at_ms=10, now_ms=11, max_age_ms=5,
    )


@contextmanager
def _poison_class(cls, field, calls):
    original = vars(cls).get(field, _MISSING)
    if field in ("__init__", "assert_shape"):
        def bad(self, *args):
            calls.append(field)
            raise AssertionError("poisoned startup method executed")

        replacement = bad
    elif field in ("__getattribute__", "__getattr__"):
        def bad(self, attr):
            calls.append((field, attr))
            raise AssertionError("poisoned startup lookup executed")

        replacement = bad
    else:
        def bad(self):
            calls.append(field)
            raise AssertionError("poisoned startup slot executed")

        replacement = property(bad)
    setattr(cls, field, replacement)
    try:
        yield
    finally:
        # Inherited __getattribute__ must be removed, NOT copied onto this
        # class as a new own attribute during test teardown.
        if original is _MISSING:
            delattr(cls, field)
        else:
            setattr(cls, field, original)


@pytest.mark.parametrize(
    "field",
    (
        "component_id", "schema_revision", "assert_shape",
        "__init__", "__getattribute__", "__getattr__",
    ),
)
def test_poisoned_requirement_refused_before_first_field_read(field):
    state = _fixture()
    calls = []
    with _poison_class(lease.SyntheticReadinessRequirement, field, calls):
        with pytest.raises(
            lease.SyntheticStartupLeaseRejected,
            match="requirement descriptor changed before review",
        ):
            _review(state)
        assert calls == []


@pytest.mark.parametrize(
    "field",
    (
        "snapshot_digest", "required_components", "captured_at_ms",
        "checked_at_ms", "__init__", "__getattribute__", "__getattr__",
    ),
)
def test_poisoned_result_refused_before_snapshot_integrity_callback(field):
    state = _fixture()
    calls = []
    with _poison_class(lease.SyntheticStartupLeaseReview, field, calls):
        with pytest.raises(
            lease.SyntheticStartupLeaseRejected,
            match="result constructor or descriptor changed",
        ):
            _review(state)
        assert calls == []


def test_clean_startup_lease_remains_denial_only_after_dependency_review():
    result = _review(_fixture())
    assert result.required_components == ("memory", "planner")
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False
