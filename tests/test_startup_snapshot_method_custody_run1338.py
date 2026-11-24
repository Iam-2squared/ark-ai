"""Run1338: startup snapshot method substitution cannot forge READY leases.

The probes and forged result are synthetic. This test does not activate
startup, dispatch, notifications, devices, credentials or a live backend.
"""

from __future__ import annotations

import pytest
import ark.startup_readiness_lease_review as lease
import ark.startup_readiness_review as readiness


@pytest.mark.parametrize(
    "method_name",
    ("_assert_integrity", "state", "root_blockers"),
)
def test_replaced_snapshot_method_is_rejected_before_probe_iteration(
    monkeypatch, method_name: str,
) -> None:
    calls: list[str] = []
    consumed: list[str] = []

    def substituted(*_args, **_kwargs):
        calls.append(method_name)
        return None

    monkeypatch.setattr(
        readiness.StartupSnapshot,
        method_name,
        substituted,
    )

    def probes():
        consumed.append("started")
        yield readiness.StartupComponent("memory", schema_revision="v1")

    with pytest.raises(
        ValueError,
        match="startup constructor authority changed",
    ):
        readiness.evaluate_startup_readiness(probes())

    assert consumed == []
    assert calls == []


def test_lease_review_rejects_replaced_snapshot_integrity_before_read(
    monkeypatch,
) -> None:
    # A forged digest must not be accepted merely because a replacement
    # _assert_integrity returns without checking the component graph.
    component = readiness.ComponentResult(
        "memory",
        (),
        readiness.ReadinessState.READY,
        readiness.ReadinessState.READY,
        None,
        "memory-v1",
    )
    snapshot = readiness.StartupSnapshot(
        (component,),
        "startup_" + "0" * 64,
    )
    requirements = (
        lease.SyntheticReadinessRequirement("memory", "memory-v1"),
    )
    calls: list[object] = []

    def substituted(self):
        calls.append(self)
        return None

    monkeypatch.setattr(
        readiness.StartupSnapshot,
        "_assert_integrity",
        substituted,
    )

    with pytest.raises(
        lease.SyntheticStartupLeaseRejected,
        match="startup lease source descriptor changed",
    ):
        lease.review_synthetic_startup_lease(
            snapshot,
            requirements,
            captured_at_ms=100,
            now_ms=101,
            max_age_ms=10,
        )

    assert calls == []
