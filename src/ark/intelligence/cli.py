"""Opt-in V2 CLI; mock remains the safe default."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from ..config import load_config
from ..logging import SessionLogger
from ..models import EchoBackend
from .contracts import Capabilities, TaskMode
from .engine import Intelligence
from .runtime import local_engine


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ARK V2: explicit local runtime or mock demo")
    parser.add_argument("--mode", choices=list(TaskMode), default="concise")
    parser.add_argument("--backend", choices=("mock", "llama-cpp"), default="mock")
    parser.add_argument("--config", help="existing V1 TOML configuration; required for llama-cpp")
    args = parser.parse_args(argv)
    if args.backend == "llama-cpp" and not args.config:
        parser.error("--config is required for llama-cpp")
    if args.backend == "mock" and args.config:
        parser.error("--config requires --backend llama-cpp (prevent accidental mock use)")
    logger = None
    try:
        if args.backend == "llama-cpp":
            config = load_config(args.config)
            engine = local_engine(config)
            logger = SessionLogger(config.log_directory)
            logger.write(role="event", content="V2 session started", model=engine.backend.name)
        else:
            engine = Intelligence(EchoBackend(), Capabilities(4096, True, "mock fixture"))
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        print(f"ARK startup error: {exc}")
        return 1
    label = "MOCK ONLY" if args.backend == "mock" else engine.backend.name
    print(f"ARK V2 {label}. /reset clears context; /exit quits. V2 gate pending review.")
    if logger:
        print(f"Session log: {logger.path}")

    def log(role: str, content: str) -> None:
        if logger:
            logger.write(role=role, content=content, model=engine.backend.name)

    while True:
        try:
            text = input("You> ").strip()
            if text == "/exit":
                log("event", "Session exited")
                return 0
            if text == "/reset":
                engine.reset()
                log("event", "Conversation reset; history empty")
                print("Conversation reset.")
            elif text:
                log("user", text)
                response = engine.chat(text, TaskMode(args.mode))
                log("assistant", response.text)
                print(f"ARK> {response.text}")
                print(f"Dropped turns: {response.request.context.dropped_turns}")
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            return 0
        except OSError as exc:
            print(f"ARK logging/runtime error: {exc}; session stopped.")
            return 1
        except (ValueError, RuntimeError) as exc:
            print(f"ARK error: {exc}")
            try:
                log("error", f"{type(exc).__name__}: {exc}")
            except OSError:
                return 1


if __name__ == "__main__":
    raise SystemExit(main())
