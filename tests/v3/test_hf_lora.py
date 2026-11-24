import json
from pathlib import Path

import pytest

from ark.learning import hf_lora
from ark.learning.dataset import digest
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


def test_loaded_tokenizer_must_reproduce_reviewed_chat_template_probe(tmp_path):
    probe = tmp_path / "chat-template-probe.txt"
    expected = (
        "<|user|>ARK V3 runtime template probe: user"
        "<|assistant|>ARK V3 runtime template probe: assistant"
    ).encode("utf-8")
    probe.write_bytes(expected)

    class FakeTokenizer:
        def __init__(self):
            self.calls = []

        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            self.calls.append((messages, tokenize, add_generation_prompt))
            return expected.decode("utf-8")

    tokenizer = FakeTokenizer()
    sha256 = hf_lora._verify_chat_template_probe(tokenizer, probe, digest(expected))
    assert sha256 == digest(expected)
    assert tokenizer.calls == [(
        [
            {"role": "user", "content": "ARK V3 runtime template probe: user"},
            {"role": "assistant", "content": "ARK V3 runtime template probe: assistant"},
        ],
        False,
        False,
    )]


def test_loaded_tokenizer_probe_mismatch_fails_closed_before_model_load(tmp_path):
    probe = tmp_path / "chat-template-probe.txt"
    expected = b"reviewed rendered template"
    probe.write_bytes(expected)

    class FakeTokenizer:
        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            return "different rendered template"

    with pytest.raises(hf_lora.LoRARuntimeError, match="differs from reviewed probe"):
        hf_lora._verify_chat_template_probe(FakeTokenizer(), probe, digest(expected))


def test_probe_file_replacement_between_identity_and_read_is_rejected(tmp_path, monkeypatch):
    probe = tmp_path / "chat-template-probe.txt"
    expected = b"reviewed rendered template"
    probe.write_bytes(expected)
    original = hf_lora.file_identity
    calls = 0

    def replace_after_first_identity(path, *, label=None):
        nonlocal calls
        identity = original(path, label=label)
        calls += 1
        if calls == 1:
            path.write_bytes(b"replacement template")
        return identity

    monkeypatch.setattr(hf_lora, "file_identity", replace_after_first_identity)

    class FakeTokenizer:
        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            raise AssertionError("changed probe must be rejected before tokenizer rendering")

    with pytest.raises(hf_lora.LoRARuntimeError, match="changed after identity review"):
        hf_lora._verify_chat_template_probe(FakeTokenizer(), probe, digest(expected))


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
        lambda snapshot, base_dir, chat_template_probe: (
            FakeTorch(), object(), FakeModel(), "a" * 64,
        ),
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
