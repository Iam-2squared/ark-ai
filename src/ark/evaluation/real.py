"""Fixed-suite local measurements. Never promotes a milestone automatically."""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter

from ..config import load_config
from ..intelligence import TaskMode
from ..intelligence.policy import POLICY_VERSION, system_instruction
from ..intelligence.runtime import V1_FREEZE_SHA, local_engine
from ..measurement import peak_ram_mib
from .runner import DOMAINS, source_hash
from .scoring import SCORER_VERSION, score
from .suite import SUITE_SHA256, load_suite


def _version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def run_real(config_path: str, output: Path, *, offline_attested: bool = False) -> dict:
    suite = load_suite()  # Frozen bytes are verified before loading the model.
    started = perf_counter()
    result = {
        "schema_version": 2,
        "contract_version": 1,
        "suite_id": suite["suite_id"],
        "suite_sha256": SUITE_SHA256,
        "scorer_version": SCORER_VERSION,
        "scorer_sha256": source_hash(("evaluation/scoring.py", "evaluation/coding.py")),
        "policy_version": POLICY_VERSION,
        "policy_sha256": source_hash(("intelligence/policy.py",)),
        "implementation_sha256": source_hash((
            "intelligence/engine.py", "intelligence/context.py", "intelligence/contracts.py",
            "intelligence/runtime.py", "evaluation/real.py", "models.py", "config.py",
        )),
        "timestamp": datetime.now(UTC).isoformat(),
        "measurement_kind": "real",
        "model_performance_status": "NOT_MEASURED",
        "v1_gate": "OFFICIAL_PASS",
        "v1_evidence_freeze_sha": V1_FREEZE_SHA,
        "v2_gate": "PENDING_REVIEW",
        "main_merge": "BLOCKED_PENDING_V2_REAL_REVIEW",
        "startup_success": False,
        "startup_error": None,
        "model_load_seconds": None,
        "model_identity": None,
        "configuration": None,
        "runtime": {
            "python": platform.python_version(), "platform": platform.platform(),
            "cpu": platform.processor(), "ark_ai": _version("ark-ai"),
            "llama_cpp": _version("llama-cpp-python"),
        },
        "network_disconnected_user_attested": offline_attested,
        "offline_verified_automatically": False,
        "system_instructions": {mode.value: system_instruction(mode) for mode in TaskMode},
        "measurement_notes": {
            "tokens": "Visible-output retokenization estimates; exact token fields remain null.",
            "speed": "Visible output estimate / generation wall time, includes prefill.",
            "context": "UTF-8/framing heuristic, not exact chat-template tokenization.",
            "memory": "Process lifetime peak resident memory, including native allocations.",
            "grading": "Frozen restricted scorers; low scores do not automatically fail V2.",
        },
        "cases": [],
    }
    results = result["cases"]
    try:
        config = load_config(config_path)
        result["configuration"] = asdict(config)
        if config.backend != "llama-cpp" or not config.model_path:
            raise ValueError("real evaluation requires a configured local llama-cpp model")
        path = Path(config.model_path).expanduser()
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        result["model_identity"] = {
            "name": path.name, "family": config.model_family,
            "parameter_size": config.parameter_size, "quantization": config.quantization,
            "weights_sha256": digest, "bytes": path.stat().st_size,
        }
        before_load = perf_counter()
        engine = local_engine(config)
        result["model_load_seconds"] = perf_counter() - before_load
        result["capabilities"] = asdict(engine.capabilities)
        result["startup_success"] = True
        for case in suite["cases"]:
            engine.reset()
            before = perf_counter()
            responses, error, verdict = [], None, None
            try:
                for prompt in [*case.get("setup", []), case["prompt"]]:
                    responses.append(engine.chat(prompt, TaskMode(case["mode"])))
                verdict = score(responses[-1].text, case)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            last = responses[-1] if responses and error is None else None
            results.append({
                "task_id": case["id"], "domain": case["domain"],
                "prompt": case["prompt"], "setup_prompts": case.get("setup", []),
                "scoring_contract": case, "response": last.text if last else None,
                "model_passed": verdict.passed if verdict else False,
                "fixture_passed": None,
                "failure_reason": error or (
                    verdict.reason if verdict and not verdict.passed else None
                ),
                "runtime_error": error,
                "scoring_details": verdict.details if verdict else None,
                "latency_seconds": perf_counter() - before,
                "turns": [asdict(response) for response in responses],
                "model_metrics": {
                    "first_token_seconds": last.first_token_seconds if last else None,
                    "tokens_per_second_estimate": last.tokens_per_second_estimate if last else None,
                    "completion_tokens_estimate": last.completion_tokens_estimate if last else None,
                    "prompt_tokens": None, "completion_tokens": None,
                    "prompt_tokens_estimate": (
                        last.request.context.prompt_tokens_estimate if last else None
                    ),
                    "context_utilization_estimate": (
                        last.request.context.utilization_estimate if last else None
                    ),
                },
            })
        result["model_performance_status"] = "MEASURED_PENDING_REVIEW"
    except Exception as exc:  # Preserve startup failures, including missing config/weights.
        result["startup_error"] = f"{type(exc).__name__}: {exc}"
    result["domains"] = {}
    for domain in DOMAINS:
        subset = [row for row in results if row["domain"] == domain]
        passed = sum(row["model_passed"] for row in subset)
        result["domains"][domain] = {
            "case_count": len(subset), "model_passed": passed,
            "model_pass_rate": passed / len(subset) if subset else None,
        }
    result["model_failures"] = sum(not row["model_passed"] for row in results)
    result["runtime_failure_count"] = sum(row["runtime_error"] is not None for row in results)
    result["runtime_failure_count"] += int(result["startup_error"] is not None)
    result["elapsed_seconds"] = perf_counter() - started
    try:
        result["peak_ram_mib"], result["memory_error"] = peak_ram_mib(), None
    except OSError as exc:
        result["peak_ram_mib"], result["memory_error"] = None, str(exc)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
