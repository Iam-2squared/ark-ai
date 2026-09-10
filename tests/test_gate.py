"""Gate collection is deterministic, local and fail-closed."""

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ark import gate


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "ARK Test"], cwd=root, check=True)
    (root / ".gitignore").write_text("evidence-bundles/\n", encoding="utf-8")
    config = root / "config.toml"
    config.write_text('[model]\nbackend="echo"\n[logging]\ndirectory="logs"\n', encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True)
    monkeypatch.chdir(root)
    return root, config


def start(repo, tmp_path, *, now=None):
    root, config = repo
    return gate.start_bundle(config, tmp_path / "bundles", now=now)


def session_rows(started: datetime) -> list[dict]:
    def row(offset, role, content):
        return {
            "timestamp": (started + timedelta(seconds=offset)).isoformat(),
            "role": role,
            "content": content,
            "model": "fixture.gguf",
        }

    return [
        row(1, "event", "Local UI V2 session started"),
        row(2, "user", "合言葉は青いりんごです"),
        row(3, "assistant", "覚えました"),
        row(4, "user", "合言葉は？"),
        row(5, "assistant", "青いりんご"),
        row(6, "event", gate.RESET_EVENT),
        row(7, "user", "未指定と答えて"),
        row(8, "assistant", "未指定"),
    ]


def test_start_is_unique_and_captures_separate_identity(repo, tmp_path):
    now = datetime.now(UTC) - timedelta(seconds=10)
    first = start(repo, tmp_path, now=now)
    second = start(repo, tmp_path, now=now)
    assert first != second
    state = json.loads((first / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "INCOMPLETE"
    assert state["identity"]["head"] == json.loads(
        (first / "git.json").read_text(encoding="utf-8")
    )["head"]
    assert (first / "screenshots/CHECKLIST.md").is_file()
    assert not Path("evidence-bundles").exists()


def test_stale_config_is_rejected_and_recorded(repo, tmp_path):
    bundle = start(repo, tmp_path)
    config = repo[1]
    config.write_text(config.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
    with pytest.raises(gate.GateError, match="stale"):
        gate.ensure_fresh(bundle)
    state = json.loads((bundle / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "INCOMPLETE" and "stale" in state


def test_mock_regressions_use_existing_engines_and_never_overwrite(repo, tmp_path):
    bundle = start(repo, tmp_path)
    gate.run_regressions(bundle, offline_attested=False, mock=True)
    state = json.loads((bundle / "state.json").read_text(encoding="utf-8"))
    assert state["phases"]["regressions"]
    assert state["regression_summary"]["measurement_kind"] == "mock"
    assert json.loads((bundle / "regressions/v1.json").read_text())["failure_count"] == 0
    with pytest.raises(gate.GateError, match="will not be overwritten"):
        gate.run_regressions(bundle, offline_attested=False, mock=True)


def test_candidates_are_content_and_window_validated_but_not_auto_copied(repo, tmp_path):
    now = datetime.now(UTC) - timedelta(seconds=10)
    bundle = start(repo, tmp_path, now=now)
    logs = tmp_path / "logs"
    logs.mkdir()
    valid = logs / "valid.jsonl"
    write_jsonl(valid, session_rows(now))
    invalid = logs / "newest.jsonl"
    write_jsonl(invalid, session_rows(now)[:3])
    candidates = gate.collect_session(bundle, logs, None)
    assert {item["filename"]: item["valid"] for item in candidates} == {
        "newest.jsonl": False,
        "valid.jsonl": True,
    }
    assert list((bundle / "sessions").iterdir()) == []
    gate.collect_session(bundle, logs, valid)
    assert (bundle / "sessions/valid.jsonl").read_bytes() == valid.read_bytes()
    with pytest.raises(gate.GateError):
        gate.collect_session(bundle, logs, tmp_path / "outside.jsonl")


def test_reset_validation_preserves_utf8_original(tmp_path):
    now = datetime.now(UTC) - timedelta(seconds=10)
    path = tmp_path / "session.jsonl"
    write_jsonl(path, session_rows(now))
    original = path.read_bytes()
    result = gate.validate_reset_session(path, now)
    assert result["valid"] and result["reset_event"] and result["post_reset_turn"]
    assert path.read_bytes() == original


def test_false_recall_without_setup_is_rejected(tmp_path):
    now = datetime.now(UTC) - timedelta(seconds=10)
    path = tmp_path / "session.jsonl"
    rows = session_rows(now)
    del rows[1:3]
    write_jsonl(path, rows)
    assert not gate.validate_reset_session(path, now)["valid"]


def test_finalize_separates_attestation_and_never_auto_passes(repo, tmp_path, monkeypatch):
    now = datetime.now(UTC) - timedelta(seconds=10)
    bundle = start(repo, tmp_path, now=now)
    logs = tmp_path / "logs"
    logs.mkdir()
    session = logs / "session.jsonl"
    write_jsonl(session, session_rows(now))
    gate.collect_session(bundle, logs, session)
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 8 + (800).to_bytes(4, "big")
                    + (600).to_bytes(4, "big"))
    monkeypatch.setattr(gate, "_regressions_pass", lambda bundle: True)
    specs = [f"{kind}={png}" for kind in sorted(gate.SCREENSHOT_KINDS)]
    status = gate.finalize(
        bundle, screenshots=specs, supplied_attestations=set(gate.ATTESTATIONS),
        non_interactive=True,
    )
    assert status == "READY_FOR_REVIEW"
    report = (bundle / "TARGET_PC_REPORT.md").read_text(encoding="utf-8")
    assert "OFFICIAL PASS: **NOT DECLARED**" in report
    assert (bundle / "manifest.sha256").is_file()
    env = json.loads((bundle / "environment.json").read_text())
    attest = json.loads((bundle / "human-attestations.json").read_text())
    assert env["human_offline_attested"] is None
    assert attest["answers"]["physical_offline"] is True


def test_noninteractive_missing_evidence_stays_incomplete(repo, tmp_path):
    bundle = start(repo, tmp_path)
    assert gate.finalize(
        bundle, screenshots=[], supplied_attestations=set(), non_interactive=True
    ) == "INCOMPLETE"
    assert "OFFICIAL PASS: **NOT DECLARED**" in (
        bundle / "TARGET_PC_REPORT.md"
    ).read_text(encoding="utf-8")


def test_screenshot_finalization_can_resume_without_overwriting(repo, tmp_path):
    bundle = start(repo, tmp_path)
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    header = b"\x89PNG\r\n\x1a\n" + b"x" * 8
    first.write_bytes(header + (10).to_bytes(4, "big") + (20).to_bytes(4, "big"))
    second.write_bytes(header + (30).to_bytes(4, "big") + (40).to_bytes(4, "big"))
    gate.finalize(
        bundle, screenshots=[f"ready={first}"], supplied_attestations=set(),
        non_interactive=True,
    )
    gate.finalize(
        bundle, screenshots=[f"error={second}"], supplied_attestations=set(),
        non_interactive=True,
    )
    rows = json.loads((bundle / "screenshots.json").read_text(encoding="utf-8"))
    assert {row["kind"] for row in rows} == {"ready", "error"}
    assert (bundle / "screenshots/first.png").read_bytes() == first.read_bytes()
