import hashlib
from pathlib import Path

import pytest

from ark.learning.dataset import ContaminationGuard, LearningCandidate, build_dataset
from ark.learning.training import MockTrainingBackend, StopRequired, TrainingConfig


def test_completion_contract_bytes_frozen():
    path = Path(__file__).resolve().parents[2] / "docs/v3/CONTRACT.md"
    expected = (path.parent / "CONTRACT.sha256").read_text().strip()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_no_real_method_through_mock(tmp_path):
    config = TrainingConfig("base", "a" * 64, "b" * 64, "c" * 40, "versions", "CPU", method="lora")
    with pytest.raises(StopRequired):
        MockTrainingBackend().train(None, config, tmp_path / "run")
    assert not (tmp_path / "run").exists()


def test_case_sensitive_targets_not_silently_deduplicated():
    fields = dict(
        source_type="human_authored",
        source_reference="owned:test",
        input="Repeat label",
        model_response="",
        evaluation="reviewed",
        rejection_reason="",
        provenance="owned",
        created_at="2026-09-09T00:00:00Z",
        reviewer="test fixture",
        source_sha256="a" * 64,
        rights="owned",
        approved=True,
        independent=True,
        split="train",
        group="g",
    )
    a = LearningCandidate(candidate_id="a", approved_target="Widget", **fields)
    b = LearningCandidate(candidate_id="b", approved_target="widget", **fields)
    with pytest.raises(RuntimeError, match="conflicting"):
        build_dataset([a, b], ContaminationGuard((), ()))
