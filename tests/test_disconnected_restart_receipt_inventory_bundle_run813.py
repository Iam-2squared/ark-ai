"""All disconnected Planner evidence must agree before publishing a HOLD bundle."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_restart_receipt_inventory_bundle as bundle_module
from ark.agency.contracts import Effect, StepState
from ark.agency.disconnected_dependency_quarantine_projection import (
    DisconnectedDependencyClaim,
    review_disconnected_dependency_quarantine,
)
from ark.agency.planner_journal_review import SyntheticPlanRecovery, SyntheticPlanTail
from ark.agency.synthetic_write_quarantine_matrix_review import (
    SyntheticWriteStoreObservation,
)

_TOPOLOGY = "plan_" + "a" * 64
_TAIL = SyntheticPlanTail(
    _TOPOLOGY, 0, "pevt_" + "b" * 64, "pstate_" + "c" * 64, -1,
)
_CLAIMS = (
    DisconnectedDependencyClaim("a", Effect.WRITE, StepState.RUNNING),
    DisconnectedDependencyClaim("b", Effect.READ, StepState.PENDING, ("a",)),
    DisconnectedDependencyClaim("c", Effect.READ, StepState.RUNNING),
)


def _inputs():
    write_ids = ("a",)
    rows = (
        SyntheticWriteStoreObservation(
            "a", "running", "present", "absent", "unavailable",
        ),
    )
    dependency = review_disconnected_dependency_quarantine(
        topology_digest=_TOPOLOGY,
        claims=_CLAIMS,
        independently_expected_write_ids=write_ids,
        observations=rows,
    )
    recovered = SyntheticPlanRecovery(
        _TAIL,
        (
            ("a", "running", 0),
            ("b", "pending", 0),
            ("c", "running", 0),
        ),
        ("a", "c"),
    )
    return {
        "recovered": recovered,
        "retained_tail": _TAIL,
        "claims": _CLAIMS,
        "independently_expected_write_ids": write_ids,
        "observations": rows,
        "dependency": dependency,
    }


def test_full_offline_receipt_bundle_never_enables_dispatch_or_replay() -> None:
    data = _inputs()
    receipt = bundle_module.review_disconnected_restart_receipt_bundle(**data)
    assert receipt == bundle_module.review_disconnected_restart_receipt_bundle(**data)
    assert receipt.topology_digest == _TOPOLOGY
    assert receipt.event_hash == _TAIL.event_hash
    assert receipt.matrix_digest == data["dependency"].matrix_digest
    assert receipt.quarantine_digest == data["dependency"].digest
    assert receipt.held_step_ids == ("a", "b", "c")
    assert receipt.unknown_step_ids == ("a", "c")
    assert len(receipt.bundle_sha256) == 64
    assert len(receipt.detached_review_sha256) == 64
    assert len(receipt.restart_review_sha256) == 64
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.independent_inventory_verified is False
    assert receipt.external_outcome_verified is False


@pytest.mark.parametrize(
    "damage",
    (
        "wrong-inventory", "missing-write", "extra-write", "wrong-observation",
        "changed-store", "changed-dependency", "changed-hold", "changed-matrix",
        "changed-journal", "stale-retained", "unknown-omitted",
        "wrong-step-state", "changed-claim-dependency", "reordered-claims",
        "wrong-types", "empty-claims", "wrong-topology", "inexact-row",
    ),
)
def test_nonmatching_inventory_journal_and_dag_are_denied(damage: str) -> None:
    data = _inputs()
    if damage == "wrong-inventory":
        data["independently_expected_write_ids"] = ("z",)
    elif damage == "missing-write":
        data["independently_expected_write_ids"] = ()
    elif damage == "extra-write":
        data["independently_expected_write_ids"] = ("a", "b")
    elif damage == "wrong-observation":
        data["observations"] = (replace(data["observations"][0], step_id="z"),)
    elif damage == "changed-store":
        data["observations"] = (replace(data["observations"][0], reservation="absent"),)
    elif damage == "changed-dependency":
        data["dependency"] = replace(data["dependency"], digest="f" * 64)
    elif damage == "changed-hold":
        bad = replace(data["dependency"].holds[1], reason="HOLD_UNAUTHORIZED_MOCK_REVIEW")
        data["dependency"] = replace(
            data["dependency"],
            holds=(data["dependency"].holds[0], bad, data["dependency"].holds[2]),
        )
    elif damage == "changed-matrix":
        data["dependency"] = replace(
            data["dependency"], matrix_digest="quarantine_" + "f" * 64,
        )
    elif damage == "changed-journal":
        data["recovered"] = replace(
            data["recovered"],
            tail=replace(_TAIL, event_hash="pevt_" + "f" * 64),
        )
    elif damage == "stale-retained":
        data["retained_tail"] = replace(_TAIL, event_hash="pevt_" + "f" * 64)
    elif damage == "unknown-omitted":
        data["recovered"] = replace(
            data["recovered"], ambiguous_running_steps=("c",),
        )
    elif damage == "wrong-step-state":
        data["recovered"] = replace(
            data["recovered"],
            step_statuses=(
                ("a", "pending", 0), ("b", "pending", 0), ("c", "running", 0),
            ),
        )
    elif damage == "changed-claim-dependency":
        data["claims"] = (
            _CLAIMS[0], replace(_CLAIMS[1], depends_on=()), _CLAIMS[2],
        )
    elif damage == "reordered-claims":
        data["claims"] = tuple(reversed(_CLAIMS))
    elif damage == "wrong-types":
        data["independently_expected_write_ids"] = ["a"]
    elif damage == "empty-claims":
        data["claims"] = ()
    elif damage == "wrong-topology":
        data["dependency"] = replace(
            data["dependency"], topology_digest="plan_" + "f" * 64,
        )
    elif damage == "inexact-row":
        data["observations"] = (("a", "running", "present", "absent", "unavailable"),)
    with pytest.raises(bundle_module.DisconnectedRestartReceiptBundleRejected):
        bundle_module.review_disconnected_restart_receipt_bundle(**data)


@pytest.mark.parametrize("changed", ("callee", "bundle-result"))
def test_original_pipeline_and_denial_descriptors_are_pinned_before_use(
    monkeypatch: pytest.MonkeyPatch, changed: str,
) -> None:
    data = _inputs()
    with monkeypatch.context() as patch:
        if changed == "callee":
            patch.setattr(
                bundle_module.digest_module, "review_detached_dependency_digest",
                lambda **kwargs: (_ for _ in ()).throw(
                    AssertionError("replaced verifier must not execute")
                ),
            )
        else:
            patch.setattr(
                bundle_module.DisconnectedRestartReceiptBundle,
                "dispatch_authorized",
                property(lambda _: True),
            )
        with pytest.raises(
            bundle_module.DisconnectedRestartReceiptBundleRejected,
            match="protocol changed",
        ):
            bundle_module.review_disconnected_restart_receipt_bundle(**data)
