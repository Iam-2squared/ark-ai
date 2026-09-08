"""Fixed V1 infrastructure cases; semantic and physical offline gates need review."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .cli import build_backend
from .config import load_config
from .core import ArkCore
from .measurement import peak_ram_mib

PROMPTS = (
    ("prompt", "Reply with exactly: ARK_OK"),
    ("reasoning", "If all ravens are birds and Kuro is a raven, what is Kuro?"),
    ("coding", "Write a Python function that returns the square of an integer."),
    ("japanese", "日本語で短く自己紹介してください。"),
    ("memory_setup", "この会話の合言葉は青いりんごです。覚えてください。"),
    ("memory_recall", "先ほどの合言葉は何ですか？"),
)


def _version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def run(
    config_path: str | None, output: Path, *, offline_attested: bool = False,
    cpu: str | None = None, ram_gib: float | None = None,
) -> dict[str, object]:
    started = time.perf_counter()
    result: dict[str, object] = {
        "schema_version": 2, "suite": "v1-final-gate-1",
        "timestamp": datetime.now(UTC).isoformat(),
        "platform": platform.platform(), "python": platform.python_version(),
        "cpu": cpu or platform.processor() or None,
        "ram_gib_user_reported": ram_gib,
        "runtime_versions": {p: _version(p) for p in ("ark-ai", "llama-cpp-python")},
        "network_disconnected_user_attested": offline_attested,
        "offline_verified_automatically": False,
        "semantic_review": {"japanese": "pending", "multi_turn": "pending"},
        "v1_final_gate": "pending_human_review",
        "startup_success": False, "startup_error": None,
        "cases": [], "success_rate": 0.0,
        "measurement_notes": {
            "success_rate": "Nonempty responses only; not correctness or V1 PASS.",
            "tokens": "Retokenized visible output estimate; excludes hidden/special tokens.",
            "speed": "Estimated visible output tokens / generation wall time, includes prefill.",
            "first_token": "Time to first nonempty streamed text, including prefill.",
            "memory": "Process lifetime peak resident memory, includes native allocations.",
            "echo": "Mock output is never evidence of model ability or real-model offline PASS.",
        },
    }
    cases = []
    try:
        config = load_config(config_path)
        result["configuration"] = asdict(config)
        result["system_prompt"] = ArkCore.__dataclass_fields__["system_prompt"].default
        path = Path(config.model_path).expanduser() if config.model_path else None
        if config.backend == "llama-cpp" and path is not None:
            with path.open("rb") as handle:
                digest = hashlib.file_digest(handle, "sha256").hexdigest()
            result["model_file"] = {
                "filename": path.name, "bytes": path.stat().st_size, "sha256": digest,
            }
        before_load = time.perf_counter()
        backend = build_backend(config)
        result["model_load_seconds"] = time.perf_counter() - before_load
        result["model"] = backend.name
        result["test_backend"] = config.backend == "echo"
        result["startup_success"] = True
        core = ArkCore(backend=backend, generation=config.generation)
        for category, prompt in PROMPTS:
            if category != "memory_recall":
                core.reset()
            before = time.perf_counter()
            try:
                response, error = core.chat(prompt), None
            except Exception as exc:
                response, error = "", f"{type(exc).__name__}: {exc}"
            cases.append({
                "category": category, "prompt": prompt, "response": response,
                "latency_seconds": time.perf_counter() - before,
                "success": error is None and bool(response), "error": error,
                "generation": _metrics(backend) if error is None else None,
            })
        result["success_rate"] = sum(bool(c["success"]) for c in cases) / len(PROMPTS)
    except Exception as exc:
        result["startup_error"] = f"{type(exc).__name__}: {exc}"
    result["cases"] = cases
    result["failure_count"] = sum(not c["success"] for c in cases) + int(
        result["startup_error"] is not None
    )
    result["elapsed_seconds"] = time.perf_counter() - started
    try:
        result["peak_ram_mib"] = peak_ram_mib()
        result["memory_error"] = None
    except OSError as exc:
        result["peak_ram_mib"], result["memory_error"] = None, str(exc)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _metrics(backend: object) -> dict[str, object] | None:
    metrics = getattr(backend, "last_metrics", None)
    if metrics is None:
        return None
    return {
        "elapsed_seconds": metrics.elapsed_seconds,
        "first_token_seconds": metrics.first_token_seconds,
        "completion_tokens_estimate": metrics.completion_tokens,
        "tokens_per_second_estimate": metrics.tokens_per_second,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ARK V1 benchmark")
    parser.add_argument("--config", help="path to config.toml")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/latest.json"))
    parser.add_argument("--offline-attested", action="store_true",
                        help="User confirms all network connections were physically disconnected")
    parser.add_argument("--cpu", help="Exact CPU name, if automatic identification is insufficient")
    parser.add_argument("--ram-gib", type=float, help="Installed RAM, user reported")
    args = parser.parse_args(argv)
    result = run(args.config, args.output, offline_attested=args.offline_attested,
                 cpu=args.cpu, ram_gib=args.ram_gib)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success_rate"] == 1.0 and result["memory_error"] is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
