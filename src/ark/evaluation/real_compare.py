"""Validate and compare complete real baselines using the frozen scorers."""

from __future__ import annotations

from .runner import DOMAINS, source_hash
from .scoring import SCORER_VERSION, score
from .suite import SUITE_SHA256, load_suite


def _validate(report: dict) -> dict:
    suite = load_suite()
    if (
        report["schema_version"] != 2 or report["measurement_kind"] != "real"
        or report["contract_version"] != 1
        or report["suite_sha256"] != SUITE_SHA256
        or report["suite_id"] != suite["suite_id"]
        or report["scorer_version"] != SCORER_VERSION
        or report["scorer_sha256"] != source_hash(("evaluation/scoring.py", "evaluation/coding.py"))
    ):
        raise ValueError("unknown real evidence contract")
    if not report["startup_success"] or report["startup_error"] is not None:
        raise ValueError("startup failure is not a complete baseline")
    if report["model_performance_status"] != "MEASURED_PENDING_REVIEW":
        raise ValueError("real measurement status missing")
    identity = report["model_identity"]
    digest = identity["weights_sha256"]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("invalid model hash")
    if not identity["name"] or identity["bytes"] <= 0:
        raise ValueError("missing model identity")
    expected = {case["id"]: case for case in suite["cases"]}
    rows = {}
    for row in report["cases"]:
        key = row["task_id"]
        if key not in expected or key in rows:
            raise ValueError("duplicate or unknown task ID")
        case = expected[key]
        if (row["scoring_contract"] != case or row["prompt"] != case["prompt"]
                or row["domain"] != case["domain"]
                or row["setup_prompts"] != case.get("setup", [])):
            raise ValueError("modified task or scoring contract")
        if type(row["model_passed"]) is not bool or row["fixture_passed"] is not None:
            raise ValueError("invalid real outcome")
        if row["runtime_error"] is not None:
            if row["model_passed"] or row["response"] is not None:
                raise ValueError("runtime error cannot claim a successful response")
        else:
            verdict = score(row["response"], case)
            if verdict.passed != row["model_passed"]:
                raise ValueError("stored score disagrees with frozen scorer")
            if len(row["turns"]) != len(case.get("setup", [])) + 1:
                raise ValueError("missing generation turns")
            if row["turns"][-1]["text"] != row["response"]:
                raise ValueError("response and generation evidence disagree")
        if bool(row["failure_reason"]) == row["model_passed"]:
            raise ValueError("failure reason and outcome disagree")
        rows[key] = row
    if rows.keys() != expected.keys():
        raise ValueError("incomplete real task evidence")
    if report["model_failures"] != sum(not row["model_passed"] for row in rows.values()):
        raise ValueError("inconsistent model failure count")
    if report["runtime_failure_count"] != sum(
        row["runtime_error"] is not None for row in rows.values()
    ):
        raise ValueError("inconsistent runtime failure count")
    for domain in DOMAINS:
        subset = [row for row in rows.values() if row["domain"] == domain]
        passed = sum(row["model_passed"] for row in subset)
        if report["domains"][domain] != {
            "case_count": len(subset), "model_passed": passed,
            "model_pass_rate": passed / len(subset),
        }:
            raise ValueError("inconsistent real domain summary")
    return rows


def compare_real(baseline: dict, candidate: dict) -> dict:
    old, new = _validate(baseline), _validate(candidate)
    differences = {
        key: {"baseline": baseline[key], "candidate": candidate[key]}
        for key in ("model_identity", "configuration", "runtime", "policy_sha256",
                    "implementation_sha256")
        if baseline[key] != candidate[key]
    }
    regressions = [key for key in old if old[key]["model_passed"] and not new[key]["model_passed"]]
    return {
        "comparison_kind": "real_model_regression", "compatible": True,
        "regressions": regressions,
        "improvements": [key for key in old if not old[key]["model_passed"]
                         and new[key]["model_passed"]],
        "regression_detected": bool(regressions),
        "candidate_fixture_failures": 0,
        "candidate_runtime_failures": candidate["runtime_failure_count"],
        "candidate_memory_error": candidate["memory_error"],
        "metadata_differences": differences,
        "controlled_comparison": not any(
            key in differences for key in ("model_identity", "configuration", "runtime")
        ),
        "model_quality_delta": {
            domain: candidate["domains"][domain]["model_pass_rate"]
            - baseline["domains"][domain]["model_pass_rate"] for domain in DOMAINS
        },
        "v2_gate": "PENDING_REVIEW", "main_merge": "BLOCKED_PENDING_V2_REAL_REVIEW",
    }
