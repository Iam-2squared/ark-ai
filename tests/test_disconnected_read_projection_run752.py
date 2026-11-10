"""Read-only cross-review contract for detached and mixed READ recovery.

No mock-ready label authorizes a backend, automatic replay, external outcome
or verified historical provenance. All identities and hashes are synthetic.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ark.agency import disconnected_read_projection_review as module
from ark.agency.disconnected_read_recovery_schedule import ReadRecoveryStep

_REQ = "req_" + "a" * 32
_PLAN = "plan_" + "b" * 64
_A = "step_" + "1" * 16
_B = "step_" + "2" * 16
_C = "step_" + "3" * 16
_D = "step_" + "4" * 16
_HASH = "c" * 64


def _step(name, state="NOT_STARTED", deps=(), operation="math.sum"):
    return ReadRecoveryStep(
        name, operation, deps, state,
        _HASH if state == "SUCCEEDED" else None,
    )


@pytest.mark.parametrize(
    ("state", "root_code", "child_code"),
    (
        ("NOT_STARTED", "READY_MOCK_ONLY", "WAIT_DEPENDENCY"),
        ("RUNNING", "QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN"),
        ("UNKNOWN", "QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN"),
        ("FAILED", "TERMINAL_FAILURE", "HOLD_FAILED"),
        ("SUCCEEDED", "COMPLETE_UNVERIFIED", "READY_MOCK_ONLY"),
    ),
)
def test_projection_reconciles_two_read_only_state_machines(
    state, root_code, child_code,
):
    steps = (
        _step(_A, state),
        _step(_B, deps=(_A,), operation="text.stats"),
        _step(_C, operation="json.inspect"),
    )
    read = module._ORIGINAL_SCHEDULE(_REQ, steps)
    projection = module.review_disconnected_read_projection(_REQ, _PLAN, steps)
    assert projection.request_id == _REQ
    assert projection.plan_id == _PLAN
    assert projection.read_schedule_digest == read.schedule_digest
    assert len(projection.mixed_fence_digest) == 64
    assert len(projection.review_sha256) == 64
    assert tuple(x.disposition for x in read.decisions) == (
        root_code, child_code, "READY_MOCK_ONLY",
    )
    expected = (_C,)
    if state == "NOT_STARTED":
        expected = (_A, _C)
    if state == "SUCCEEDED":
        expected = (_B, _C)
    assert projection.ready_step_ids == expected
    assert projection == module.review_disconnected_read_projection(
        _REQ, _PLAN, steps,
    )
    assert projection.dispatch_authorized is False
    assert projection.automatic_replay_authorized is False
    assert projection.authenticated_history is False
    with pytest.raises(FrozenInstanceError):
        projection.review_sha256 = "0" * 64


def test_diamond_terminal_outweighs_uncertainty_and_independent_read_is_ready():
    steps = (
        _step(_A, "SUCCEEDED"),
        _step(_B, "FAILED", (_A,), "text.stats"),
        _step(_C, "UNKNOWN", (_A,), "text.find"),
        _step(_D, deps=(_B, _C), operation="json.inspect"),
    )
    result = module.review_disconnected_read_projection(_REQ, _PLAN, steps)
    assert result.ready_step_ids == ()
    assert result.dispatch_authorized is False


@pytest.mark.parametrize("bad_steps", (
    (),
    [_step(_A)],
    (_step(_A, operation="filesystem.delete"),),
    (_step(_A), _step(_B, "SUCCEEDED", (_A,))),
    (_step(_A), _step(_B, deps=(_C,))),
))
def test_projection_rejects_invalid_or_unproven_history(bad_steps):
    with pytest.raises(module.ReadRecoveryProjectionRejected):
        module.review_disconnected_read_projection(_REQ, _PLAN, bad_steps)


@pytest.mark.parametrize(
    ("request_id", "plan_id"),
    (
        ("req_invalid", _PLAN),
        (_REQ, "plan_invalid"),
        (True, _PLAN),
        (_REQ, None),
    ),
)
def test_projection_rejects_untyped_or_invalid_group_identifiers(
    request_id, plan_id,
):
    with pytest.raises(module.ReadRecoveryProjectionRejected):
        module.review_disconnected_read_projection(
            request_id, plan_id, (_step(_A),),
        )


def test_replaced_classifier_rejected_before_synthetic_input_is_used(monkeypatch):
    called = []

    def forged(*args):
        called.append(args)
        raise AssertionError("forged classifier called")

    monkeypatch.setattr(module, "schedule_detached_read_recovery", forged)
    with pytest.raises(module.ReadRecoveryProjectionRejected, match="protocol changed"):
        module.review_disconnected_read_projection(
            _REQ, _PLAN, (_step(_A),),
        )
    assert called == []


@pytest.mark.parametrize("field", ("state", "operation", "result_sha256"))
def test_original_read_slots_checked_before_private_claim_access(
    monkeypatch, field,
):
    observed = []
    existing_step = _step(_A)

    def exfiltrating_property(self):
        observed.append(field)
        raise AssertionError("malicious accessor invoked")

    with monkeypatch.context() as patch:
        patch.setattr(ReadRecoveryStep, field, property(exfiltrating_property))
        with pytest.raises(
            module.ReadRecoveryProjectionRejected, match="descriptor changed",
        ):
            module.review_disconnected_read_projection(
                _REQ, _PLAN, (existing_step,),
            )
    assert observed == []
    assert module.review_disconnected_read_projection(
        _REQ, _PLAN, (_step(_A),),
    ).dispatch_authorized is False


@pytest.mark.parametrize("dependency", ("_STATE", "_CODES"))
def test_mutated_disposition_projection_mapping_cannot_define_new_authority(
    monkeypatch, dependency,
):
    with monkeypatch.context() as patch:
        patch.setattr(module, dependency, {"READY_MOCK_ONLY": "COMPLETE_UNVERIFIED"})
        with pytest.raises(
            module.ReadRecoveryProjectionRejected, match="protocol changed",
        ):
            module.review_disconnected_read_projection(
                _REQ, _PLAN, (_step(_A),),
            )
