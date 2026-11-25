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
from ark.learning.identity import build_hf_snapshot_identity

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
        b"<|user|>ARK V3 runtime template probe: user"
        b"<|assistant|>ARK V3 runtime template probe: assistant"
    )
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


def _write_staging_snapshot(base_dir: Path, probe: Path) -> dict:
    base_dir.mkdir()
    (base_dir / "config.json").write_text("{}", encoding="utf-8")
    (base_dir / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (base_dir / "tokenizer.json").write_text('{"version":"1"}', encoding="utf-8")
    (base_dir / "model.safetensors").write_bytes(b"synthetic-model-bytes")
    probe.write_bytes(b"synthetic-rendered-chat-template")
    identity = build_hf_snapshot_identity(
        base_dir,
        model_id="Qwen/Qwen3-4B-Instruct-2507",
        revision="1" * 40,
        chat_template_probe=probe,
    )
    return {
        "base": {
            "model_id": identity["model_id"],
            "revision": identity["revision"],
            "file_sha256_manifest": identity["base_file_manifest_sha256"],
        },
        "tokenizer": {
            "file_sha256_manifest": identity["tokenizer_file_manifest_sha256"],
            "chat_template_probe_sha256": identity["chat_template_probe_sha256"],
        },
    }


def test_verified_snapshot_is_staged_and_rehashed_before_loader_use(tmp_path):
    base_dir = tmp_path / "source-model"
    probe = tmp_path / "probe.txt"
    snapshot = _write_staging_snapshot(base_dir, probe)

    owner, staged = hf_lora._stage_verified_hf_snapshot(snapshot, base_dir, probe)
    try:
        assert staged != base_dir
        assert staged.is_dir()
        staged_identity = build_hf_snapshot_identity(
            staged,
            model_id=snapshot["base"]["model_id"],
            revision=snapshot["base"]["revision"],
            chat_template_probe=probe,
        )
        assert staged_identity["base_file_manifest_sha256"] == (
            snapshot["base"]["file_sha256_manifest"]
        )
        assert staged_identity["tokenizer_file_manifest_sha256"] == (
            snapshot["tokenizer"]["file_sha256_manifest"]
        )
    finally:
        owner.cleanup()
    assert not staged.exists()


def test_changed_bytes_during_staging_are_denied_and_temp_tree_is_removed(
    tmp_path,
    monkeypatch,
):
    base_dir = tmp_path / "source-model"
    probe = tmp_path / "probe.txt"
    snapshot = _write_staging_snapshot(base_dir, probe)

    original_copy = hf_lora._copy_verified_snapshot_file

    def replace_source_then_copy(source, destination, *, expected_sha256, expected_bytes):
        source.write_bytes(b"unreviewed replacement")
        original_copy(
            source,
            destination,
            expected_sha256=expected_sha256,
            expected_bytes=expected_bytes,
        )

    monkeypatch.setattr(hf_lora, "_copy_verified_snapshot_file", replace_source_then_copy)
    with pytest.raises(hf_lora.LoRARuntimeError, match="base snapshot bytes changed while staging"):
        hf_lora._stage_verified_hf_snapshot(snapshot, base_dir, probe)


def test_model_and_tokenizer_load_only_from_verified_staged_tree(tmp_path, monkeypatch):
    base_dir = tmp_path / "source-model"
    probe = tmp_path / "probe.txt"
    snapshot = _write_staging_snapshot(base_dir, probe)
    loader_paths = []

    class FakeCuda:
        @staticmethod
        def is_available():
            return True

        @staticmethod
        def is_bf16_supported():
            return True

    class FakeTorch:
        cuda = FakeCuda()
        bfloat16 = object()

    class FakeTokenizer:
        @classmethod
        def from_pretrained(cls, path, **kwargs):
            loader_paths.append(Path(path))
            return cls()

        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            return probe.read_text(encoding="utf-8")

    class FakeModel:
        @classmethod
        def from_pretrained(cls, path, **kwargs):
            loader_paths.append(Path(path))
            return cls()

        def to(self, device):
            assert device == "cuda"
            return self

    class FakeLoraConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    def get_peft_model(model, config):
        return model

    monkeypatch.setattr(
        hf_lora,
        "_runtime_imports",
        lambda: (FakeTorch, FakeLoraConfig, get_peft_model, FakeModel, FakeTokenizer),
    )
    _, _, _, verified_probe_sha256, owner = hf_lora._build_model_and_tokenizer(
        snapshot,
        base_dir,
        probe,
    )
    try:
        assert len(loader_paths) == 2
        assert loader_paths[0] == loader_paths[1]
        assert loader_paths[0] != base_dir
        assert loader_paths[0].is_dir()
        assert verified_probe_sha256 == snapshot["tokenizer"]["chat_template_probe_sha256"]
    finally:
        owner.cleanup()
    assert not loader_paths[0].exists()


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
            FakeTorch(), object(), FakeModel(), "a" * 64, None,
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
