"""Synthetic infrastructure fixtures only, never actual approved training examples."""

import json
from dataclasses import replace

import pytest

from ark.learning.dataset import (
    ContaminationGuard,
    DatasetArtifact,
    LearningCandidate,
    build_dataset,
    canonical,
    digest,
)
from ark.learning.gate import SimulationEvidence, simulate_gate
from ark.learning.registry import CandidateRegistry
from ark.learning.training import (
    MockTrainingBackend,
    RealTrainingBackend,
    StopRequired,
    TrainingConfig,
)


def example(identifier="a", **changes):
    values = dict(
        candidate_id=identifier,
        source_type="human_authored",
        source_reference="unit-test-only:independent-synthetic",
        input="Say marmalade only",
        model_response="marmalade",
        evaluation="fixture quality check",
        approved_target="marmalade",
        rejection_reason="",
        provenance="owned synthetic fixture",
        created_at="2026-09-09T00:00:00Z",
        reviewer="test-reviewer-not-real-approval",
        source_sha256="a" * 64,
        rights="owned",
        approved=True,
        independent=True,
        split="train",
        group="group-a",
    )
    values.update(changes)
    return LearningCandidate(**values)


def dataset():
    return build_dataset(
        [
            example(),
            example(
                "b",
                input="Say blueberry only",
                approved_target="blueberry",
                split="validation",
                group="group-b",
            ),
        ],
        ContaminationGuard.frozen_v2(),
    )


def config(data):
    return TrainingConfig(
        "mock-not-weights",
        "b" * 64,
        data.sha256,
        "c" * 40,
        "synthetic dependencies",
        "synthetic CPU",
    )


def test_deterministic_dataset_and_counts():
    rows = [
        example(),
        example(
            "b",
            input="Say blueberry only",
            approved_target="blueberry",
            split="validation",
            group="group-b",
        ),
    ]
    a = build_dataset(rows, ContaminationGuard.frozen_v2())
    b = build_dataset(rows[::-1], ContaminationGuard.frozen_v2())
    assert a == b
    assert a.summary["accepted"] == 2
    assert a.summary["train_examples"] == a.summary["validation_examples"] == 1
    assert a.summary["dataset_bytes"] == len(a.payload)


@pytest.mark.parametrize(
    "changes",
    [
        {"approved": False},
        {"independent": False},
        {"reviewer": ""},
        {"source_sha256": "bad"},
        {"rights": "unknown"},
        {"split": "evaluation"},
        {"created_at": "2026-09-09"},
        {"schema_version": 99},
        {"source_type": "private_conversation"},
        {"rejection_reason": "unreviewed"},
    ],
)
def test_unapproved_invalid_candidates_rejected(changes):
    result = build_dataset([example(**changes)], ContaminationGuard.frozen_v2())
    assert result.summary["accepted"] == 0 and result.summary["rejected"] == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"input": "Compute 3/4 + 1/8. Return only a fraction or decimal."},
        {"input": "Compute 3/4 + 1/8. Return only a fraction or decimal!"},
        {"approved_target": "7/8"},
        {"source_reference": "evidence/v2/raw/v2-real-1.json"},
        {"provenance": "copied from evaluation/scoring.py"},
    ],
)
def test_contamination_rejection(changes):
    result = build_dataset([example(**changes)], ContaminationGuard.frozen_v2())
    assert result.summary["contamination_rejects"] == 1


def test_dedup_and_conflicts():
    guard = ContaminationGuard.frozen_v2()
    result = build_dataset([example(), example("b")], guard)
    assert result.summary["duplicates"] == 1
    for changes in ({"approved_target": "other"}, {"split": "validation"}):
        with pytest.raises(RuntimeError, match="conflicting"):
            build_dataset([example(), example("b", **changes)], guard)
    with pytest.raises(RuntimeError, match="group crosses"):
        build_dataset([example(), example("b", input="Unrelated task", split="validation")], guard)
    with pytest.raises(ValueError, match="duplicate candidate"):
        build_dataset([example(), example()], guard)


def test_mock_receipt_is_not_model_and_refuses_overwrite(tmp_path):
    data = dataset()
    run = MockTrainingBackend().train(data, config(data), tmp_path / "run")
    assert run.artifact.kind == "mock_receipt"
    assert run.measurement_kind == "mock" and all(v is None for v in run.metrics.values())
    with pytest.raises(ValueError, match="new explicit"):
        MockTrainingBackend().train(data, config(data), tmp_path / "run")
    with pytest.raises(StopRequired):
        RealTrainingBackend().train(data, config(data), tmp_path / "real")
    assert not (tmp_path / "real").exists()


def test_tampered_dataset_refused(tmp_path):
    data = dataset()
    with pytest.raises(ValueError, match="hash mismatch"):
        MockTrainingBackend().train(
            replace(data, payload=b"tampered"), config(data), tmp_path / "run"
        )
    payload = canonical(
        {
            "schema_version": 1,
            "examples": [
                {**json.loads(data.payload)["examples"][0], "approved": False},
                json.loads(data.payload)["examples"][1],
            ],
        }
    )
    forged = DatasetArtifact(payload, digest(payload), {})
    with pytest.raises(ValueError, match="validation"):
        MockTrainingBackend().train(forged, config(forged), tmp_path / "run")


def test_registry_append_only_and_artifact_verification(tmp_path):
    registry = CandidateRegistry(tmp_path)
    data = dataset()
    cfg = config(data)
    registry.create("candidate-one", cfg)
    with pytest.raises(FileExistsError):
        registry.create("candidate-one", cfg)
    registry.transition("candidate-one", "TRAINING")
    run = MockTrainingBackend().train(data, cfg, tmp_path / "run")
    registry.transition("candidate-one", "TRAINED", run=run)
    registry.transition("candidate-one", "EVALUATING")
    with pytest.raises(StopRequired):
        registry.transition("candidate-one", "PROMOTION_ELIGIBLE")
    registry.transition("candidate-one", "REJECTED", reason="simulation only")
    registry.transition("candidate-one", "ARCHIVED")
    assert registry.latest("candidate-one")["status"] == "ARCHIVED"
    with pytest.raises(ValueError):
        registry.transition("candidate-one", "TRAINING")
    assert len(list((tmp_path / "candidate-one").glob("*.json"))) == 6
    with pytest.raises(ValueError):
        registry.create("../escape", cfg)


def test_registry_rejects_bad_artifact(tmp_path):
    data = dataset()
    cfg = config(data)
    registry = CandidateRegistry(tmp_path)
    registry.create("item", cfg)
    registry.transition("item", "TRAINING")
    run = MockTrainingBackend().train(data, cfg, tmp_path / "run")
    with pytest.raises(ValueError, match="hash mismatch"):
        registry.transition(
            "item", "TRAINED", run=replace(run, artifact=replace(run.artifact, sha256="d" * 64))
        )
    assert registry.latest("item")["status"] == "TRAINING"


def evidence(**changes):
    values = dict(
        baseline_runs=((True, False),) * 2,
        candidate_runs=((True, True),) * 2,
        controlled=True,
        provenance_reviewed=True,
        contamination_suspected=False,
        runtime_failures=0,
        memory_error=False,
    )
    values.update(changes)
    return SimulationEvidence(**values)


@pytest.mark.parametrize(
    "changes",
    [
        {"controlled": False},
        {"provenance_reviewed": False},
        {"contamination_suspected": True},
        {"runtime_failures": 1},
        {"memory_error": True},
        {"candidate_runs": ((False, True),) * 2},
        {"candidate_runs": ((True, False),) * 2},
        {"candidate_runs": ((True, True), (True, False))},
        {"baseline_runs": ()},
    ],
)
def test_promotion_policy_fail_closed(changes):
    result = simulate_gate(evidence(**changes))
    assert result["simulation_decision"] == "REJECT"
    assert not result["automatic_promotion"]


def test_simulation_cannot_promote_real_model():
    result = simulate_gate(evidence())
    assert result["simulation_decision"] == "ELIGIBLE_IN_SIMULATION_ONLY"
    assert result["model_promotion_status"] == "NOT_EVALUATED"
    assert result["v3_gate"] == "NOT_PASSED"
    with pytest.raises(StopRequired):
        simulate_gate(evidence(measurement_kind="real"))
