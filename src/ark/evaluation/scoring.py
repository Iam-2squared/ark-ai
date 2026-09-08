"""Deterministic, versioned scoring rules for the frozen V2 foundation suite."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction

from .coding import test_code

SCORER_VERSION = "ark-scorers-1"


@dataclass(frozen=True)
class Score:
    passed: bool
    reason: str
    details: list[dict] | None = None


def normalized_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip().casefold()


def number(text: str) -> Fraction:
    text = normalized_text(text)
    if len(text) > 128 or not re.fullmatch(r"[+-]?\d+(?:\.\d+)?(?:/[+-]?\d+)?", text):
        raise ValueError("expected only an integer, decimal or fraction")
    return Fraction(text)


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def score(response: str, case: dict) -> Score:
    if not response.strip():
        return Score(False, "empty_response")
    if len(response.encode("utf-8")) > 4096:
        return Score(False, "response_too_large")
    try:
        rule = case["scorer"]
        if rule == "number":
            passed = number(response) == number(case["expected"])
        elif rule == "exact":
            passed = normalized_text(response) == normalized_text(case["expected"])
        elif rule == "json":
            actual = json.loads(response, object_pairs_hook=_unique_object)
            passed = json.dumps(actual, sort_keys=True) == json.dumps(
                case["expected"], sort_keys=True
            )
        elif rule == "code":
            passed, reason, details = test_code(response, case)
            return Score(passed, reason, details)
        else:
            return Score(False, "unknown_scoring_rule")
        return Score(passed, "passed" if passed else "answer_mismatch")
    except (ValueError, ArithmeticError, RecursionError) as exc:
        return Score(False, f"invalid_answer: {type(exc).__name__}: {exc}")
