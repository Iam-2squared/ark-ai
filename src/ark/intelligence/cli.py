"""Mock-only opt-in V2 CLI while the V1 hardware gate is pending."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from ..models import EchoBackend
from .contracts import Capabilities, TaskMode
from .engine import Intelligence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ARK V2 mock demo (not real AI inference)")
    parser.add_argument("--mode", choices=list(TaskMode), default="concise")
    args = parser.parse_args(argv)
    engine = Intelligence(EchoBackend(), Capabilities(4096, True, "mock fixture"))
    print("ARK V2 MOCK ONLY. /reset clears context; /exit quits. Real-model gate locked.")
    while True:
        try:
            text = input("You> ").strip()
            if text == "/exit":
                return 0
            if text == "/reset":
                engine.reset()
                print("Conversation reset.")
            elif text:
                response = engine.chat(text, TaskMode(args.mode))
                print(f"MOCK> {response.text}")
                print(f"Dropped turns: {response.request.context.dropped_turns}")
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            return 0
        except (ValueError, RuntimeError) as exc:
            print(f"ARK error: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
