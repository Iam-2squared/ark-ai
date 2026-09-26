import json
from pathlib import Path

import pytest

from ark.learning.execution import ExecutionBlocked
from ark.learning.hf_lora import (
    HfLoRAFullRun,
    HfLoRAPreflightBackend,
    deterministic_training_order,
)

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


def test_wall_time_guard_aborts_full_run_before_candidate_save(monkeypatch, tmp_path):
    import ark.learning.hf_lora as module

    class BudgetSentinel:
        def __init__(self, timeout_minutes):
            assert timeout_minutes == 5

        def check(self, phase):
            if phase == "training-microbatch-2-start":
                raise RuntimeError("approved wall-clock timeout exceeded")

    class FakeCuda:
        @staticmethod
        def reset_peak_memory_stats():
            return None

        @staticmethod
        def synchronize():
            return None

    class FakeTorch:
        cuda = FakeCuda()

    class FakeModel:
        def train(self):
            return None

    class FakeOptimizer:
        def zero_grad(self, set_to_none=True):
            return None

        def step(self):
            return None

    monkeypatch.setattr(
        module,
        "validate_experiment_001",
        lambda snapshot, authorization_scope: "a" * 64,
    )
    monkeypatch.setattr(module, "WallTimeBudget", BudgetSentinel)
    rows = [{"candidate_id": f"ex-{index}"} for index in range(120)]
    monkeypatch.setattr(module, "_verify_local_identities", lambda *args, **kwargs: (rows, []))
    monkeypatch.setattr(
        module,
        "_build_model_and_tokenizer",
        lambda snapshot, base_dir: (FakeTorch(), object(), FakeModel()),
    )
    monkeypatch.setattr(module, "_pretokenize", lambda tokenizer, ordered: [(None, None)] * 120)
    monkeypatch.setattr(
        module,
        "_optimizer",
        lambda torch, model, learning_rate: (FakeOptimizer(), [object()]),
    )
    monkeypatch.setattr(module, "_single_backward", lambda *args, **kwargs: 1.0)

    output = tmp_path / "candidate"
    runner = HfLoRAFullRun(
        base_dir=tmp_path / "base",
        dataset_path=tmp_path / "dataset.json",
        chat_template_probe=tmp_path / "probe.txt",
        output_dir=output,
    )
    snapshot = {
        "budget": {"wall_clock_timeout_minutes": 5},
        "method": {"seed": 42, "gradient_accumulation": 8, "learning_rate": 0.0001},
    }
    with pytest.raises(RuntimeError, match="wall-clock timeout exceeded"):
        runner.run(snapshot)
    assert not output.exists()
