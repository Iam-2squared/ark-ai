"""Regression tests: queue aging must use actual activity starts, not old run age."""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ci_queue_review.py"
_SPEC = importlib.util.spec_from_file_location("ci_queue_review_run459", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
audit = _MODULE.audit_actions_queue
Rejected = _MODULE.QueueReviewRejected
NOW = "2026-10-27T04:00:00Z"
OLD = "2026-10-27T01:00:00Z"
RECENT = "2026-10-27T03:59:30Z"


def data(*, run_started=OLD, step_started=OLD, status="in_progress"):
    run = {"id": 20, "head_sha": "a" * 40, "status": status,
           "created_at": OLD, "run_started_at": run_started}
    job = {"id": 30, "run_id": 20, "status": "in_progress", "steps": [
        {"name": "Run pytest", "status": "in_progress", "started_at": step_started}
    ]}
    return {"total_count": 1, "workflow_runs": [run]}, ({"jobs": [job]},)


def test_actual_old_step_is_reported_without_authority():
    runs, jobs = data()
    result = audit(runs, jobs, captured_at=NOW)
    assert result["stale_pytest_jobs"] == [
        {"run_id": 20, "job_id": 30, "step_age_seconds": 10800,
         "run_age_seconds": 10800}
    ]
    assert result["stale_runs"] == [
        {"run_id": 20, "status": "in_progress", "age_seconds": 10800}
    ]
    assert result["all_six_matrix_green_verified"] is False
    assert result["runner_action_authorized"] is False


def test_old_run_recent_step_not_reported_as_stuck():
    runs, jobs = data(step_started=RECENT)
    result = audit(runs, jobs, captured_at=NOW)
    assert result["stale_pytest_jobs"] == []
    assert result["stale_runs"]  # Run really has been active for 3h.


def test_old_queued_time_does_not_age_just_started_run():
    runs, jobs = data(run_started=RECENT, step_started=RECENT)
    result = audit(runs, jobs, captured_at=NOW)
    assert result["stale_runs"] == []
    assert result["stale_pytest_jobs"] == []


def test_unknown_pytest_start_not_promoted_to_stale():
    runs, jobs = data(step_started=None)
    result = audit(runs, jobs, captured_at=NOW)
    assert result["stale_pytest_jobs"] == []
    assert result["unknown_pytest_start_jobs"] == [{"run_id": 20, "job_id": 30}]


def test_unknown_run_start_is_separate_from_age():
    runs, jobs = data(run_started=None, step_started=OLD)
    result = audit(runs, jobs, captured_at=NOW)
    assert result["stale_runs"] == []
    assert result["unknown_run_start_ids"] == [20]
    assert result["stale_pytest_jobs"][0]["step_age_seconds"] == 10800


def test_old_queued_run_stale_from_created_time():
    runs = {"total_count": 3, "workflow_runs": [
        {"id": 12, "head_sha": "b" * 40, "status": "queued", "created_at": OLD}
    ]}
    result = audit(runs, (), captured_at=NOW)
    assert result["stale_runs"] == [
        {"run_id": 12, "status": "queued", "age_seconds": 10800}
    ]
    assert not result["coverage_complete"]


@pytest.mark.parametrize("field,value", [
    ("run_started_at", "2026-10-27T00:59:59Z"),
    ("run_started_at", "2026-10-27T04:00:01Z"),
    ("run_started_at", "2026-10-27T03:59:30+0000"),
    ("status", True),
    ("id", True),
    ("head_sha", "A" * 40),
])
def test_invalid_run_carriers_rejected(field, value):
    runs, jobs = data()
    runs["workflow_runs"][0][field] = value
    with pytest.raises(Rejected):
        audit(runs, jobs, captured_at=NOW)


@pytest.mark.parametrize("started", [
    "2026-10-27T00:59:59Z", "2026-10-27T04:00:01Z",
    "2026-10-27T03:00:00+0000", "2026-02-30T02:00:00Z", True,
])
def test_invalid_pytest_start_rejected(started):
    runs, jobs = data(step_started=started)
    with pytest.raises(Rejected):
        audit(runs, jobs, captured_at=NOW)


def test_completed_run_cannot_contain_running_job():
    runs, jobs = data(status="completed")
    with pytest.raises(Rejected, match="inconsistent"):
        audit(runs, jobs, captured_at=NOW)


def test_unknown_or_duplicate_jobs_rejected():
    runs, jobs = data()
    jobs = (jobs[0], jobs[0])
    with pytest.raises(Rejected, match="duplicate"):
        audit(runs, jobs, captured_at=NOW)


def test_invalid_future_capture_rejected():
    runs, jobs = data()
    with pytest.raises(Rejected):
        audit(runs, jobs, captured_at="2026-10-27T00:00:00Z")


def test_empty_valid_batch_is_not_green():
    result = audit({"total_count": 0, "workflow_runs": []}, (), captured_at=NOW)
    assert result["coverage_complete"]
    assert result["all_six_matrix_green_verified"] is False
    assert result["reviewed_jobs"] == 0
