"""Command-line chat for ARK V1."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .config import ArkConfig, load_config
from .core import ArkCore
from .logging import SessionLogger
from .models import EchoBackend, LlamaCppBackend, ModelBackend


def build_backend(config: ArkConfig) -> ModelBackend:
    if config.backend == "echo":
        return EchoBackend()
    if config.backend != "llama-cpp":
        raise ValueError(f"unsupported backend: {config.backend}")
    if not config.model_path:
        raise ValueError("set model.path in config.toml or ARK_MODEL_PATH")
    return LlamaCppBackend(
        config.model_path, context_size=config.context_size, threads=config.threads
    )


def run_chat(config: ArkConfig) -> int:
    backend = build_backend(config)
    core = ArkCore(backend=backend, generation=config.generation)
    logger = SessionLogger(config.log_directory)
    print(f"ARK V1 ready ({backend.name}). Commands: /reset, /exit")
    while True:
        try:
            user_text = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            return 0
        if not user_text:
            continue
        if user_text in {"/exit", "/quit"}:
            return 0
        if user_text == "/reset":
            core.reset()
            print("Conversation reset.")
            continue
        logger.write(role="user", content=user_text, model=backend.name)
        try:
            response = core.chat(user_text)
        except Exception as exc:  # the CLI is the user-facing error boundary
            print(f"ARK error: {exc}", file=sys.stderr)
            continue
        logger.write(role="assistant", content=response, model=backend.name)
        print(f"ARK> {response}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ARK AI local chat")
    parser.add_argument("--config", help="path to a TOML configuration file")
    parser.add_argument("--backend", choices=("llama-cpp", "echo"), help="override backend")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.backend:
            config = ArkConfig(**{**config.__dict__, "backend": args.backend})
        return run_chat(config)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
