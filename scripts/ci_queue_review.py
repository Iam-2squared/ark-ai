"""Offline GitHub Actions queue audit from already-exported JSON snapshots.

Never connects to GitHub, starts a runner, cancels/retries a run, reads logs or
modifies an action. No authorization, billing or CI outcome is inferred.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_STATES = frozenset(("queued", "in_progress", "completed", "waiting", "pending"))
_MAX_RUNS = 1000
_MAX_JOBS = 4000


class QueueReviewRejected(ValueError):
    """Input snapshot is missing exact, bounded run/job metadata."""


def _instant(raw: object) -> datetime:
    if type(raw) is not str or len(raw) != 20 or not raw.endswith("Z"):
        raise QueueReviewRejected("UTC timestamp must be YYYY-MM-DDTHH:MM:SSZ")
    try:
        result = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise QueueReviewRejected("invalid UTC timestamp") from exc
    if result.strftime("%Y-%m-%dT%H:%M:%SZ") != raw:
        raise QueueReviewRejected("noncanonical UTC timestamp")
    return result


def audit_actions_queue(
    runs: dict, job_groups: tuple[dict, ...], *, captured_at: str,
    stale_after_seconds: int = 3600,
) -> dict:
    """Summarize stale runs/pytest jobs, never judge unexecuted CI as GREEN."""
    if (
        type(runs) is not dict or type(runs.get("total_count")) is not int
        or type(runs.get("workflow_runs")) is not list
        or not 0 <= runs["total_count"]
        or len(runs["workflow_runs"]) > _MAX_RUNS
        or len(runs["workflow_runs"]) > runs["total_count"]
        or type(job_groups) is not tuple or len(job_groups) > _MAX_RUNS
        or type(stale_after_seconds) is not int
        or not 60 <= stale_after_seconds <= 86400
    ):
        raise QueueReviewRejected("invalid bounded Actions batch")
    now = _instant(captured_at)
    selected = {}
    status_counts = {"queued": 0, "in_progress": 0, "completed": 0,
                     "waiting": 0, "pending": 0}
    stale_runs = []
    for run in runs["workflow_runs"]:
        if type(run) is not dict:
            raise QueueReviewRejected("invalid run metadata")
        ident, sha, status, created = (
            run.get("id"), run.get("head_sha"), run.get("status"),
            run.get("created_at"),
        )
        if (
            type(ident) is not int or ident <= 0 or ident in selected
            or type(sha) is not str or _SHA.fullmatch(sha) is None
            or type(status) is not str or status not in _STATES
        ):
            raise QueueReviewRejected("duplicate or invalid run identity/state")
        age = int((now - _instant(created)).total_seconds())
        if age < 0:
            raise QueueReviewRejected("run creation occurs after audit snapshot")
        selected[ident] = (sha, status, age)
        status_counts[status] += 1
        if status in ("queued", "in_progress") and age >= stale_after_seconds:
            stale_runs.append((ident, status, age))

    stuck_pytest = []
    observed_jobs = set()
    job_count = 0
    for batch in job_groups:
        if type(batch) is not dict or type(batch.get("jobs")) is not list:
            raise QueueReviewRejected("invalid exported job group")
        job_count += len(batch["jobs"])
        if job_count > _MAX_JOBS:
            raise QueueReviewRejected("job review budget exceeded")
        for job in batch["jobs"]:
            if type(job) is not dict:
                raise QueueReviewRejected("invalid job record")
            jid, rid, status = job.get("id"), job.get("run_id"), job.get("status")
            if (
                type(jid) is not int or jid <= 0 or jid in observed_jobs
                or type(rid) is not int or rid not in selected
                or type(status) is not str or status not in _STATES
                or type(job.get("steps")) is not list or len(job["steps"]) > 64
            ):
                raise QueueReviewRejected("unknown, duplicate or invalid job")
            observed_jobs.add(jid)
            _, parent_status, age = selected[rid]
            if parent_status == "completed" and status in ("queued", "in_progress"):
                raise QueueReviewRejected("unfinished job under completed run")
            active_pytest = [
                step for step in job["steps"]
                if type(step) is dict and step.get("name") == "Run pytest"
                and step.get("status") == "in_progress"
            ]
            if len(active_pytest) > 1:
                raise QueueReviewRejected("duplicate pytest step in job")
            if active_pytest and status == "in_progress" and age >= stale_after_seconds:
                stuck_pytest.append((rid, jid, age))

    return {
        "observed_at_utc": captured_at,
        "stale_threshold_seconds": stale_after_seconds,
        "reported_total_runs": runs["total_count"],
        "sampled_runs": len(selected),
        "sampled_status_counts": status_counts,
        "reviewed_jobs": job_count,
        "stale_runs": [
            {"run_id": ident, "status": status, "age_seconds": age}
            for ident, status, age in sorted(stale_runs)
        ],
        "stale_pytest_jobs": [
            {"run_id": rid, "job_id": jid, "run_age_seconds": age}
            for rid, jid, age in sorted(stuck_pytest)
        ],
        "coverage_complete": len(selected) == runs["total_count"],
        "all_six_matrix_green_verified": False,
        "runner_action_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-json", type=Path, required=True)
    parser.add_argument("--jobs-json", type=Path, required=True)
    parser.add_argument("--captured-at-utc", required=True)
    arguments = parser.parse_args()
    for file in (arguments.runs_json, arguments.jobs_json):
        if not file.is_file() or file.stat().st_size > 1_048_576:
            parser.error("export must be existing bounded local JSON")
    runs = json.loads(arguments.runs_json.read_text(encoding="utf-8"))
    job_groups = json.loads(arguments.jobs_json.read_text(encoding="utf-8"))
    result = audit_actions_queue(runs, job_groups, captured_at=arguments.captured_at_utc)
    print(json.dumps(result, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
