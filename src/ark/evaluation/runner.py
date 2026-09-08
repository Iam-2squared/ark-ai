"""Mock-only V2 evaluation runner. Real inference requires a future reviewed gate change."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from time import perf_counter

from ..intelligence import Capabilities, Intelligence, TaskMode
from ..intelligence.policy import POLICY_VERSION, system_instruction
from ..measurement import peak_ram_mib
from ..models import GenerationConfig
from .mock import FixtureBackend
from .scoring import SCORER_VERSION, score
from .suite import SUITE_SHA256, load_suite

DOMAINS = ("conversation", "context", "math", "reasoning", "coding")
MODEL_METRICS = (
    "first_token_seconds",
    "tokens_per_second",
    "peak_ram_mib",
    "prompt_tokens",
    "completion_tokens",
    "context_utilization",
)


def source_hash(names: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for name in names:
        digest.update(name.encode() + b"\0")
        digest.update(files("ark").joinpath(name).read_bytes())
    return digest.hexdigest()


def run_mock(output: Path) -> dict:
    suite = load_suite()
    generation = GenerationConfig(max_tokens=256, temperature=0, seed=42)
    capabilities = Capabilities(
        4096, True, "scripted fixture configuration", coding_evidence="fixture_only_not_measured"
    )
    backend = FixtureBackend()
    engine = Intelligence(backend, capabilities, generation=generation)
    results = []
    started = perf_counter()
    for case in suite["cases"]:
        engine.reset()
        before = perf_counter()
        responses = []
        error = None
        verdict = None
        try:
            for prompt in [*case.get("setup", []), case["prompt"]]:
                responses.append(engine.chat(prompt, TaskMode(case["mode"])))
            verdict = score(responses[-1].text, case)
        except Exception as exc:  # Evidence boundary: one failure does not discard the suite.
            error = f"{type(exc).__name__}: {exc}"
        results.append(
            {
                "task_id": case["id"],
                "domain": case["domain"],
                "prompt": case["prompt"],
                "setup_prompts": case.get("setup", []),
                "scoring_contract": case,
                "response": responses[-1].text if responses and error is None else None,
                "fixture_passed": verdict.passed if verdict else False,
                "model_passed": None,
                "model_metrics": dict.fromkeys(MODEL_METRICS),
                "failure_reason": error
                or (verdict.reason if verdict and not verdict.passed else None),
                "scoring_details": verdict.details if verdict else None,
                "infrastructure_latency_seconds": perf_counter() - before,
                "infrastructure_turns": [asdict(response) for response in responses],
            }
        )
    summaries = {}
    for domain in DOMAINS:
        subset = [r for r in results if r["domain"] == domain]
        passed = sum(r["fixture_passed"] for r in subset)
        summaries[domain] = {
            "case_count": len(subset),
            "fixture_passed": passed,
            "fixture_pass_rate": passed / len(subset),
            "model_pass_rate": None,
        }
    result = {
        "schema_version": 1,
        "contract_version": 1,
        "suite_id": suite["suite_id"],
        "suite_sha256": SUITE_SHA256,
        "scorer_version": SCORER_VERSION,
        "scorer_sha256": source_hash(("evaluation/scoring.py", "evaluation/coding.py")),
        "policy_version": POLICY_VERSION,
        "policy_sha256": source_hash(("intelligence/policy.py",)),
        "implementation_sha256": source_hash(
            (
                "intelligence/engine.py",
                "intelligence/context.py",
                "intelligence/contracts.py",
                "evaluation/runner.py",
                "evaluation/mock.py",
                "models.py",
            )
        ),
        "measurement_kind": "mock",
        "model_performance_status": "NOT_MEASURED",
        "v1_gate": "PENDING_TARGET_EVIDENCE",
        "v2_gate": "NOT_PASSED",
        "real_model_evaluation": "LOCKED",
        "main_merge": "BLOCKED_PENDING_V1_PASS",
        "timestamp": datetime.now(UTC).isoformat(),
        "model_identity": {"name": backend.name, "quantization": None, "weights_sha256": None},
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "llama_cpp": None,
        },
        "configuration": {"generation": asdict(generation), "capabilities": asdict(capabilities)},
        "system_instructions": {mode.value: system_instruction(mode) for mode in TaskMode},
        "model_metrics": dict.fromkeys(MODEL_METRICS),
        "domains": summaries,
        "cases": results,
        "infrastructure_failure_count": sum(not r["fixture_passed"] for r in results),
        "model_failures": None,
        "infrastructure_elapsed_seconds": perf_counter() - started,
        "infrastructure_peak_ram_mib": peak_ram_mib(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V2 mock evaluation; real-model evaluation LOCKED")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/v2-mock.json"))
    args = parser.parse_args(argv)
    try:
        result = run_mock(args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(
        f"MOCK ONLY: {len(result['cases'])} fixture cases; "
        f"{result['infrastructure_failure_count']} failed. Model performance: NOT_MEASURED."
    )
    print(f"Evidence: {args.output}. Main merge BLOCKED; V1 target gate pending.")
    return int(result["infrastructure_failure_count"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
