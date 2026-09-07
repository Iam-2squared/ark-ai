"""Reproducible V1 benchmark runner."""

from __future__ import annotations

import argparse
import json
import platform
import resource
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from .cli import build_backend
from .config import load_config
from .core import ArkCore

PROMPTS = (
    ("prompt", "Reply with exactly: ARK_OK"),
    ("reasoning", "If all ravens are birds and Kuro is a raven, what is Kuro?"),
    ("coding", "Write a Python function that returns the square of an integer."),
    ("japanese", "日本語で短く自己紹介してください。"),
)


def run(config_path: str | None, output: Path) -> dict[str, object]:
    config = load_config(config_path)
    backend = build_backend(config)
    cases: list[dict[str, object]] = []
    started = time.perf_counter()
    for category, prompt in PROMPTS:
        core = ArkCore(backend=backend, generation=config.generation)
        before = time.perf_counter()
        try:
            response = core.chat(prompt)
            error = None
        except Exception as exc:
            response, error = "", f"{type(exc).__name__}: {exc}"
        cases.append(
            {
                "category": category,
                "prompt": prompt,
                "response": response,
                "latency_seconds": round(time.perf_counter() - before, 4),
                "success": error is None and bool(response),
                "error": error,
                "generation": _metrics(backend),
            }
        )
    result = {
        "schema_version": 1,
        "timestamp": datetime.now(UTC).isoformat(),
        "model": backend.name,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "offline_capable": config.backend in {"echo", "llama-cpp"},
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "peak_ram_mib": round(_peak_ram_mib(), 2),
        "success_rate": sum(bool(case["success"]) for case in cases) / len(cases),
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _metrics(backend: object) -> dict[str, object] | None:
    metrics = getattr(backend, "last_metrics", None)
    if metrics is None:
        return None
    return {
        "elapsed_seconds": round(metrics.elapsed_seconds, 4),
        "first_token_seconds": round(metrics.first_token_seconds, 4),
        "completion_tokens": metrics.completion_tokens,
        "tokens_per_second": round(metrics.tokens_per_second, 2),
    }


def _peak_ram_mib() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports KiB; macOS reports bytes.
    return value / (1024 * 1024) if platform.system() == "Darwin" else value / 1024


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ARK V1 benchmark")
    parser.add_argument("--config", help="path to config.toml")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/latest.json"))
    args = parser.parse_args(argv)
    result = run(args.config, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success_rate"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
