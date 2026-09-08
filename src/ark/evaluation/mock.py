"""Public scripted answers exclusively for infrastructure verification.

No learning, model inference, or capability measurement happens here. Answers are
kept outside the real backend and are never appended to the generation prompt.
"""

from __future__ import annotations


class FixtureBackend:
    name = "scripted-v2-fixture-NOT-A-MODEL"
    last_metrics = None

    def generate(self, messages: list[dict[str, str]], config: object) -> str:
        del config
        prompt = messages[-1]["content"]
        fixed = {
            "Compute 17 * 6. Return only the number.": "102",
            "Compute 3/4 + 1/8. Return only a fraction or decimal.": "0.875",
            "Solve 5*x - 7 = 18. Return only x as a number.": "5",
            "All ravens are birds. Kuro is a raven. Is Kuro a bird? Answer only YES or NO.": "YES",
            "A is before B. C is after B. Which is first? Answer only A, B, or C.": "A",
            "「準備完了」とだけ日本語で答えてください。": "準備完了",
            (
                "Return a JSON object with exactly one key status whose string value is ready."
            ): '{"status": "ready"}',
        }
        if prompt in fixed:
            return fixed[prompt]
        if prompt.startswith("Write Python function square(n)"):
            return "def square(n):\n    return n * n"
        if prompt.startswith("Write Python function is_even(n)"):
            return "def is_even(n):\n    return n % 2 == 0"
        if prompt.startswith("Write Python function larger(a, b)"):
            return "def larger(a, b):\n    return a if a > b else b"
        users = [m["content"] for m in messages[:-1] if m["role"] == "user"]
        if prompt == "先ほどの合言葉だけを答えてください。":
            return "紫の時計" if any("紫の時計" in p for p in users) else "unknown"
        if prompt == "What is the current project name? Return only the name.":
            for previous in reversed(users):
                if "Birch" in previous:
                    return "Birch"
                if "Cedar" in previous:
                    return "Cedar"
            return "unknown"
        return "Acknowledged (scripted fixture)."
