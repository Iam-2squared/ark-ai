"""Exact carrier preaccess for disconnected synthetic WRITE quarantine.

No ToolBackend, user data, approval, clock, or external effects are involved.
A frozen slotted input or result can still be retargeted at class level.
"""

from __future__ import annotations

import pytest

import ark.agency.synthetic_write_quarantine_matrix_review as matrix


def _inputs() -> tuple[
    tuple[str, ...], tuple[matrix.SyntheticWriteStoreObservation, ...],
]:
    return ("write",), (
        matrix.SyntheticWriteStoreObservation(
            "write", "pending", "absent", "absent", "absent",
        ),
    )


def _diagnose() -> matrix.SyntheticQuarantineMatrix:
    names, observations = _inputs()
    return matrix.diagnose_disconnected_write_quarantine(
        topology_digest="plan_" + "a" * 64,
        independently_expected_step_ids=names,
        observations=observations,
    )


@pytest.mark.parametrize(
    ("class_name", "field"),
    (
        ("SyntheticWriteStoreObservation", "step_id"),
        ("SyntheticWriteStoreObservation", "plan_state"),
        ("SyntheticWriteStoreObservation", "reservation"),
        ("SyntheticWriteStoreObservation", "preaction_audit"),
        ("SyntheticWriteStoreObservation", "audit_link"),
        ("SyntheticQuarantineFinding", "step_id"),
        ("SyntheticQuarantineFinding", "reasons"),
        ("SyntheticQuarantineMatrix", "topology_digest"),
        ("SyntheticQuarantineMatrix", "observed_write_step_ids"),
        ("SyntheticQuarantineMatrix", "findings"),
        ("SyntheticQuarantineMatrix", "local_digest"),
    ),
)
def test_rebound_slotted_field_is_denied_before_executable_getter(
    monkeypatch: pytest.MonkeyPatch, class_name: str, field: str,
) -> None:
    # Build the caller-owned input before installing a hostile descriptor.
    names, observations = _inputs()
    called: list[str] = []

    def hostile(_self: object) -> object:
        called.append(field)
        raise AssertionError("replaced carrier getter executed")

    target = getattr(matrix, class_name)
    with monkeypatch.context() as patch:
        patch.setattr(target, field, property(hostile))
        with pytest.raises(
            matrix.SyntheticQuarantineMatrixRejected,
            match="carrier definition changed",
        ):
            matrix.diagnose_disconnected_write_quarantine(
                topology_digest="plan_" + "a" * 64,
                independently_expected_step_ids=names,
                observations=observations,
            )
    assert called == []


@pytest.mark.parametrize("class_name", (
    "SyntheticWriteStoreObservation",
    "SyntheticQuarantineFinding",
    "SyntheticQuarantineMatrix",
))
# Replacing __new__ on a live slotted dataclass changes CPython's tp_new
# slot even after monkeypatch deletion (Python 3.11-3.13), poisoning later
# unrelated tests. The runtime still guards __new__; do not fault-inject that
# C-level slot in the shared pytest process.
@pytest.mark.parametrize("hook", (
    "__getattribute__", "__getattr__", "__init__",
))
def test_rebound_carrier_hook_fails_closed_without_invocation(
    monkeypatch: pytest.MonkeyPatch, class_name: str, hook: str,
) -> None:
    names, observations = _inputs()
    called: list[str] = []

    def hostile(*_args: object, **_kwargs: object) -> object:
        called.append(hook)
        raise AssertionError("replaced class hook executed")

    target = getattr(matrix, class_name)
    with monkeypatch.context() as patch:
        patch.setattr(target, hook, hostile, raising=False)
        with pytest.raises(
            matrix.SyntheticQuarantineMatrixRejected,
            match="carrier definition changed",
        ):
            matrix.diagnose_disconnected_write_quarantine(
                topology_digest="plan_" + "a" * 64,
                independently_expected_step_ids=names,
                observations=observations,
            )
    assert called == []


def test_valid_fixture_remains_denied_and_deterministic() -> None:
    left = _diagnose()
    right = _diagnose()
    assert left == right
    assert left.findings[0].step_id == "write"
    assert "no_external_nonexecution_proof" in left.findings[0].reasons
    assert left.dispatch_authorized is False
    assert left.automatic_replay_authorized is False
    assert left.external_outcome_known is False
    assert left.findings[0].automatic_replay_authorized is False
