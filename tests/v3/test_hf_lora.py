import json
from pathlib import Path

import pytest

from ark.learning.execution import ExecutionBlocked
from ark.learning.hf_lora import HfLoRAFullRun, HfLoRAPreflightBackend, deterministic_training_order


TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def test_training_order_is_seeded_and_input_order_independent():
    rows = [{"candidate_id": f"ex-{index}"} for index in range(20)]
    first = deterministic_training_order(rows, seed=42)
    second = deterministic_training_order(list(reversed(rows)), seed=42)
    assert [row["candidate_id"] for row in first] == [row["candidate_id"] for row in second]
    assert [row["candidate_id"] for row in first] != [row["candidate_id"] for row in rows]


def test_duplicate_training_ids_are_rejected():
    with pytest.raises(ValueError, match="unique candidate_id"):
        deterministic_training_order([{"candidate_id": "x"}, {"candidate_id": "x"}])


def test_preflight_cannot_reach_heavy_imports_from_unresolved_snapshot(tmp_path):
    snapshot = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    backend = HfLoRAPreflightBackend(
        base_dir=tmp_path / "base",
        dataset_path=tmp_path / "dataset.json",
        chat_template_probe=tmp_path / "probe.txt",
    )
    with pytest.raises(ExecutionBlocked):
        backend.run(snapshot)


def test_full_run_cannot_create_output_from_unresolved_snapshot(tmp_path):
    snapshot = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    output = tmp_path / "candidate"
    runner = HfLoRAFullRun(
        base_dir=tmp_path / "base",
        dataset_path=tmp_path / "dataset.json",
        chat_template_probe=tmp_path / "probe.txt",
        output_dir=output,
    )
    with pytest.raises(ExecutionBlocked):
        runner.run(snapshot)
    assert not output.exists()
