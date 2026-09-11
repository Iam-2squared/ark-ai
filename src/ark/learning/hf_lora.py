"""Concrete experiment-001 LoRA engine, unreachable without explicit authorization.

Heavy training dependencies are imported only inside authorized runtime methods so normal
ARK/CI remains dependency-free. Model/tokenizer loading is local-files-only; this module
never provisions compute or downloads weights.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

from .dataset import digest
from .execution import validate_experiment_001
from .identity import build_hf_snapshot_identity
from .preflight import PreflightEvidence
from .runtime_guard import WallTimeBudget


class LoRARuntimeError(RuntimeError):
    pass


def deterministic_training_order(rows: list[dict], seed: int = 42) -> list[dict]:
    if len({row.get("candidate_id") for row in rows}) != len(rows):
        raise ValueError("training rows require unique candidate_id values")
    return sorted(
        rows,
        key=lambda row: hashlib.sha256(
            f"{seed}:{row['candidate_id']}".encode()
        ).hexdigest(),
    )


def _load_dataset(path: Path, expected_sha256: str) -> tuple[list[dict], list[dict]]:
    payload = Path(path).read_bytes()
    if digest(payload) != expected_sha256:
        raise LoRARuntimeError("dataset bytes do not match frozen snapshot SHA-256")
    parsed = json.loads(payload)
    if parsed.get("schema_version") != 1 or not isinstance(parsed.get("examples"), list):
        raise LoRARuntimeError("invalid canonical dataset payload")
    train = [row for row in parsed["examples"] if row.get("split") == "train"]
    validation = [row for row in parsed["examples"] if row.get("split") == "validation"]
    if len(train) != 120 or len(validation) != 30 or len(parsed["examples"]) != 150:
        raise LoRARuntimeError("canonical experiment-001 dataset must be exactly 120/30")
    return train, validation


def _verify_local_identities(
    snapshot: dict,
    *,
    base_dir: Path,
    chat_template_probe: Path,
    dataset_path: Path,
) -> tuple[list[dict], list[dict]]:
    identity = build_hf_snapshot_identity(
        base_dir,
        model_id=snapshot["base"]["model_id"],
        revision=snapshot["base"]["revision"],
        chat_template_probe=chat_template_probe,
    )
    if identity["base_file_manifest_sha256"] != snapshot["base"]["file_sha256_manifest"]:
        raise LoRARuntimeError("local base snapshot manifest mismatch")
    if (
        identity["tokenizer_file_manifest_sha256"]
        != snapshot["tokenizer"]["file_sha256_manifest"]
    ):
        raise LoRARuntimeError("local tokenizer snapshot manifest mismatch")
    if (
        identity["chat_template_probe_sha256"]
        != snapshot["tokenizer"]["chat_template_probe_sha256"]
    ):
        raise LoRARuntimeError("chat-template probe digest mismatch")
    return _load_dataset(dataset_path, snapshot["dataset"]["canonical_sha256"])


def _runtime_imports():
    try:
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:  # pragma: no cover - training stack is intentionally absent in CI
        raise LoRARuntimeError("pinned V3 training dependencies are not installed") from exc
    return torch, LoraConfig, get_peft_model, AutoModelForCausalLM, AutoTokenizer


def _build_model_and_tokenizer(snapshot: dict, base_dir: Path):
    torch, LoraConfig, get_peft_model, AutoModelForCausalLM, AutoTokenizer = _runtime_imports()
    if not torch.cuda.is_available():
        raise LoRARuntimeError("authorized experiment-001 runtime requires CUDA GPU")
    if not torch.cuda.is_bf16_supported():
        raise LoRARuntimeError("frozen experiment-001 precision requires CUDA BF16 support")

    tokenizer = AutoTokenizer.from_pretrained(
        str(base_dir),
        local_files_only=True,
        trust_remote_code=False,
    )
    model = AutoModelForCausalLM.from_pretrained(
        str(base_dir),
        local_files_only=True,
        trust_remote_code=False,
        torch_dtype=torch.bfloat16,
    )
    model.to("cuda")
    lora = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.0,
        target_modules=["q_proj", "v_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    return torch, tokenizer, model


def _encoded_example(tokenizer, row: dict, max_length: int = 256) -> tuple[list[int], list[int]]:
    user = {"role": "user", "content": row["input"]}
    assistant = {"role": "assistant", "content": row["approved_target"]}
    prompt_ids = tokenizer.apply_chat_template(
        [user],
        tokenize=True,
        add_generation_prompt=True,
    )
    full_ids = tokenizer.apply_chat_template(
        [user, assistant],
        tokenize=True,
        add_generation_prompt=False,
    )
    if len(full_ids) > max_length:
        raise LoRARuntimeError(
            f"example {row['candidate_id']} exceeds frozen max sequence length {max_length}"
        )
    if len(prompt_ids) >= len(full_ids) or full_ids[: len(prompt_ids)] != prompt_ids:
        raise LoRARuntimeError(
            f"example {row['candidate_id']} chat-template prefix is not loss-mask compatible"
        )
    labels = list(full_ids)
    labels[: len(prompt_ids)] = [-100] * len(prompt_ids)
    return list(full_ids), labels


def _pretokenize(tokenizer, rows: list[dict]) -> list[tuple[list[int], list[int]]]:
    return [_encoded_example(tokenizer, row, max_length=256) for row in rows]


def _optimizer(torch, model, method: dict):
    """Construct AdamW from the frozen execution recipe, not library defaults."""
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if not parameters:
        raise LoRARuntimeError("LoRA model exposes no trainable parameters")
    optimizer = torch.optim.AdamW(
        parameters,
        lr=method["learning_rate"],
        betas=tuple(method["optimizer_betas"]),
        eps=method["optimizer_eps"],
        weight_decay=method["optimizer_weight_decay"],
        amsgrad=method["optimizer_amsgrad"],
        maximize=method["optimizer_maximize"],
    )
    return optimizer, parameters


def _single_backward(torch, model, encoded, *, scale: float) -> float:
    input_ids, labels = encoded
    ids = torch.tensor([input_ids], dtype=torch.long, device="cuda")
    target = torch.tensor([labels], dtype=torch.long, device="cuda")
    attention = torch.ones_like(ids)
    outputs = model(input_ids=ids, attention_mask=attention, labels=target)
    loss = outputs.loss
    if loss is None or not bool(torch.isfinite(loss).item()):
        raise LoRARuntimeError("non-finite training loss")
    (loss / scale).backward()
    return float(loss.detach().cpu().item())


class HfLoRAPreflightBackend:
    """One-step non-Candidate mechanics probe for an already-provisioned GPU."""

    def __init__(self, *, base_dir: Path, dataset_path: Path, chat_template_probe: Path):
        self.base_dir = Path(base_dir)
        self.dataset_path = Path(dataset_path)
        self.chat_template_probe = Path(chat_template_probe)

    def run(self, snapshot: dict) -> PreflightEvidence:
        validate_experiment_001(snapshot, authorization_scope="preflight")
        wall_budget = WallTimeBudget(snapshot["budget"]["wall_clock_timeout_minutes"])
        wall_budget.check("preflight-start")
        train_rows, _ = _verify_local_identities(
            snapshot,
            base_dir=self.base_dir,
            chat_template_probe=self.chat_template_probe,
            dataset_path=self.dataset_path,
        )
        wall_budget.check("preflight-local-identity")
        torch, tokenizer, model = _build_model_and_tokenizer(snapshot, self.base_dir)
        wall_budget.check("preflight-model-load")
        encoded = _encoded_example(tokenizer, deterministic_training_order(train_rows)[0])
        optimizer, _ = _optimizer(torch, model, snapshot["method"])
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        _single_backward(torch, model, encoded, scale=1.0)
        wall_budget.check("preflight-backward")
        optimizer.step()
        torch.cuda.synchronize()
        wall_budget.check("preflight-optimizer-step")
        elapsed = time.perf_counter() - started
        total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        peak = torch.cuda.max_memory_allocated() / (1024**2)
        return PreflightEvidence(
            device=torch.cuda.get_device_name(0),
            vram_gib=float(total_vram),
            base_loaded=True,
            tokenizer_probe_sha256=snapshot["tokenizer"]["chat_template_probe_sha256"],
            forward_backward_ok=True,
            optimizer_step_ok=True,
            peak_vram_mib=float(peak),
            wall_seconds=float(elapsed),
            runtime_error=None,
        )


class HfLoRAFullRun:
    """One authorized full Candidate run; never invoked by CI or normal ARK commands."""

    def __init__(
        self,
        *,
        base_dir: Path,
        dataset_path: Path,
        chat_template_probe: Path,
        output_dir: Path,
    ):
        self.base_dir = Path(base_dir)
        self.dataset_path = Path(dataset_path)
        self.chat_template_probe = Path(chat_template_probe)
        self.output_dir = Path(output_dir)

    def run(self, snapshot: dict) -> dict:
        snapshot_sha = validate_experiment_001(snapshot, authorization_scope="training")
        wall_budget = WallTimeBudget(snapshot["budget"]["wall_clock_timeout_minutes"])
        wall_budget.check("training-start")
        if (
            self.output_dir.exists()
            or self.output_dir.is_symlink()
            or not self.output_dir.parent.is_dir()
            or any(
                parent.is_symlink()
                for parent in (self.output_dir.parent, *self.output_dir.parents)
            )
        ):
            raise LoRARuntimeError(
                "Candidate output directory must be new under safe existing parents"
            )
        train_rows, _ = _verify_local_identities(
            snapshot,
            base_dir=self.base_dir,
            chat_template_probe=self.chat_template_probe,
            dataset_path=self.dataset_path,
        )
        wall_budget.check("training-local-identity")
        torch, tokenizer, model = _build_model_and_tokenizer(snapshot, self.base_dir)
        wall_budget.check("training-model-load")
        ordered = deterministic_training_order(train_rows, snapshot["method"]["seed"])
        encoded_rows = _pretokenize(tokenizer, ordered)
        wall_budget.check("training-pretokenize")
        optimizer, trainable = _optimizer(torch, model, snapshot["method"])

        accumulation = snapshot["method"]["gradient_accumulation"]
        if len(encoded_rows) % accumulation:
            raise LoRARuntimeError("training rows must divide exactly by gradient accumulation")
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        losses: list[float] = []
        optimizer_steps = 0
        model.train()
        for index, encoded in enumerate(encoded_rows, start=1):
            wall_budget.check(f"training-microbatch-{index}-start")
            losses.append(_single_backward(torch, model, encoded, scale=float(accumulation)))
            wall_budget.check(f"training-microbatch-{index}-backward")
            if index % accumulation == 0:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                optimizer_steps += 1
                wall_budget.check(f"training-optimizer-step-{optimizer_steps}")
        torch.cuda.synchronize()
        wall_budget.check("training-synchronize")
        elapsed = time.perf_counter() - started
        if optimizer_steps != 15:
            raise LoRARuntimeError("experiment-001 must execute exactly 15 optimizer steps")

        wall_budget.check("training-before-save")
        self.output_dir.mkdir()
        adapter_dir = self.output_dir / "adapter"
        model.save_pretrained(adapter_dir, safe_serialization=True)
        wall_budget.check("training-adapter-save")
        tokenizer.save_pretrained(self.output_dir / "tokenizer")
        wall_budget.check("training-tokenizer-save")
        metrics = {
            "schema_version": 1,
            "experiment_id": "v3-format-compliance-001",
            "execution_snapshot_sha256": snapshot_sha,
            "dataset_sha256": snapshot["dataset"]["canonical_sha256"],
            "optimizer_steps": optimizer_steps,
            "microbatches": len(encoded_rows),
            "mean_training_loss": math.fsum(losses) / len(losses),
            "peak_vram_mib": float(torch.cuda.max_memory_allocated() / (1024**2)),
            "wall_seconds": float(elapsed),
            "trainable_parameters": int(sum(parameter.numel() for parameter in trainable)),
            "method": dict(snapshot["method"]),
        }
        metrics_payload = (
            json.dumps(metrics, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
        ).encode()
        with (self.output_dir / "training-metrics.json").open("xb") as handle:
            handle.write(metrics_payload)
        with (self.output_dir / "execution-snapshot.json").open("xb") as handle:
            handle.write(
                (
                    json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False)
                    + "\n"
                ).encode()
            )
        wall_budget.check("training-evidence-save")
        return {
            **metrics,
            "training_metrics_sha256": digest(metrics_payload),
            "adapter_directory": str(adapter_dir),
            "authorization_scope": "training",
        }
