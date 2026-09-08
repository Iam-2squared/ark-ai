"""Strict fixture regression comparison; incompatible evidence is rejected."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .runner import DOMAINS
from .suite import SUITE_SHA256, load_suite

COMPATIBILITY = (
    "schema_version",
    "contract_version",
    "suite_id",
    "suite_sha256",
    "scorer_version",
    "scorer_sha256",
    "measurement_kind",
)


def _validated(report: dict) -> dict:
    # This advance branch can validate only its mock schema, not future real measurements.
    if report.get("measurement_kind") != "mock" or report.get("schema_version") != 1:
        raise ValueError("only schema-1 mock evidence is supported while real evaluation is locked")
    if report.get("model_performance_status") != "NOT_MEASURED":
        raise ValueError("mock report cannot claim measured model performance")
    if any(v is not None for v in report["model_metrics"].values()):
        raise ValueError("mock model metrics must remain null")
    suite = load_suite()
    if report["suite_sha256"] != SUITE_SHA256 or report["suite_id"] != suite["suite_id"]:
        raise ValueError("unknown suite identity")
    expected = {c["id"]: c["domain"] for c in suite["cases"]}
    rows = {}
    for case in report["cases"]:
        key = case["task_id"]
        if key in rows or key not in expected or case["domain"] != expected[key]:
            raise ValueError("duplicate, unknown or misclassified task ID")
        if type(case["fixture_passed"]) is not bool or case.get("model_passed") is not None:
            raise ValueError("invalid mock outcome")
        if any(v is not None for v in case["model_metrics"].values()):
            raise ValueError("mock case metrics must remain null")
        if (case["fixture_passed"] and case["failure_reason"] is not None) or (
            not case["fixture_passed"] and not case["failure_reason"]
        ):
            raise ValueError("outcome and failure reason disagree")
        rows[key] = case
    if rows.keys() != expected.keys():
        raise ValueError("incomplete task evidence")
    failures = sum(not r["fixture_passed"] for r in rows.values())
    if report["infrastructure_failure_count"] != failures:
        raise ValueError("inconsistent failure count")
    for domain in DOMAINS:
        subset = [r for r in rows.values() if r["domain"] == domain]
        passed = sum(r["fixture_passed"] for r in subset)
        s = report["domains"][domain]
        if (
            s["case_count"] != len(subset)
            or s["fixture_passed"] != passed
            or s["fixture_pass_rate"] != passed / len(subset)
            or s["model_pass_rate"] is not None
        ):
            raise ValueError("inconsistent domain summary")
    return rows


def compare(baseline: dict, candidate: dict) -> dict:
    try:
        for key in COMPATIBILITY:
            if baseline[key] != candidate[key]:
                raise ValueError(f"incompatible {key}")
        old, new = _validated(baseline), _validated(candidate)
        regressions = [
            key for key in old if old[key]["fixture_passed"] and not new[key]["fixture_passed"]
        ]
        improvements = [
            key for key in old if not old[key]["fixture_passed"] and new[key]["fixture_passed"]
        ]
        differences = {
            key: {"baseline": baseline[key], "candidate": candidate[key]}
            for key in (
                "policy_sha256",
                "implementation_sha256",
                "configuration",
                "model_identity",
                "runtime",
            )
            if baseline[key] != candidate[key]
        }
        return {
            "comparison_kind": "fixture_regression_only",
            "compatible": True,
            "regressions": regressions,
            "improvements": improvements,
            "regression_detected": bool(regressions),
            "candidate_fixture_failures": candidate["infrastructure_failure_count"],
            "metadata_differences": differences,
            "model_quality_delta": None,
            "v2_gate": "NOT_PASSED",
            "main_merge": "BLOCKED_PENDING_V1_PASS",
        }
    except (KeyError, TypeError) as exc:
        raise ValueError(f"invalid evidence schema: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare V2 fixture evidence; not model quality")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/v2-comparison.json"))
    args = parser.parse_args(argv)
    try:
        result = compare(
            json.loads(args.baseline.read_text(encoding="utf-8")),
            json.loads(args.candidate.read_text(encoding="utf-8")),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return int(result["regression_detected"] or result["candidate_fixture_failures"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
