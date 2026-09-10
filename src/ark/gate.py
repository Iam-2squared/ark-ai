"""Local, resumable evidence collection for ARK target-PC review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import secrets
import shutil
import struct
import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .benchmark import run as run_v1
from .config import load_config
from .evaluation.compare import compare
from .evaluation.runner import run_mock, source_hash
from .evaluation.scoring import SCORER_VERSION
from .evaluation.suite import SUITE_SHA256

ATTESTATIONS = {
    "physical_offline": "Physical Wi-Fi/Ethernet disconnection confirmed?",
    "ime": "Native Windows IME composition confirmed?",
    "enter": "Enter sending confirmed?",
    "shift_enter": "Shift+Enter newline confirmed?",
    "send_button": "Send button confirmed?",
    "generating_controls": "Generating-time Send/reset disabling confirmed?",
    "loading_ready": "Visual Loading to Ready transition confirmed?",
    "refresh_retention": "Conversation retention after refresh confirmed?",
}
SCREENSHOT_KINDS = {"ready", "conversation", "reset", "error"}
RESET_EVENT = "Conversation reset; history empty"


class GateError(RuntimeError):
    pass


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=False, capture_output=True, text=True, encoding="utf-8"
    )
    if check and result.returncode:
        raise GateError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def repository_root(path: Path | None = None) -> Path:
    path = path or Path.cwd()
    return Path(_git(path, "rev-parse", "--show-toplevel")).resolve()


def git_snapshot(repo: Path) -> dict[str, object]:
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
    remote = _git(repo, "config", "--get", "remote.origin.url", check=False)
    if "@" in remote and "://" in remote:
        remote = remote.split("://", 1)[0] + "://" + remote.rsplit("@", 1)[1]
    return {
        "repository": repo.name,
        "remote": remote or None,
        "branch": _git(repo, "branch", "--show-current") or None,
        "head": _git(repo, "rev-parse", "HEAD"),
        "status": status,
        "tracked_status": [line for line in status if not line.startswith("??")],
        "untracked_status": [line for line in status if line.startswith("??")],
    }


def _installed_ram_bytes() -> int | None:
    if os.name == "nt":
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                ("avail_extended", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.total_phys)
        return None
    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        return None


def environment_snapshot(*, browser: str | None, network_state: str | None) -> dict:
    return {
        "platform": platform.platform(),
        "os": platform.system(),
        "python": platform.python_version(),
        "ark_ai": _package_version("ark-ai"),
        "llama_cpp_python": _package_version("llama-cpp-python"),
        "cpu": platform.processor() or None,
        "installed_ram_bytes": _installed_ram_bytes(),
        "browser_user_reported": browser,
        "network_state_observed": network_state or "NOT_MEASURED",
        "human_offline_attested": None,
    }


def model_snapshot(config_path: Path) -> tuple[dict, dict]:
    config_path = config_path.expanduser().resolve()
    config = load_config(config_path)
    model = Path(config.model_path).expanduser().resolve() if config.model_path else None
    result = {
        "filename": model.name if model else None,
        "bytes": model.stat().st_size if model and model.is_file() else None,
        "sha256": _sha(model) if model and model.is_file() else None,
        "exists": bool(model and model.is_file()),
        "family": config.model_family,
        "parameter_size": config.parameter_size,
        "quantization": config.quantization,
        "context_size": config.context_size,
        "backend": config.backend,
    }
    config_info = {"filename": config_path.name, "sha256": _sha(config_path)}
    return result, config_info


def _identity_from(git: dict, model: dict, config: dict) -> dict:
    return {
        "head": git["head"],
        "tracked_status": git["tracked_status"],
        "config_sha256": config["sha256"],
        "model_sha256": model["sha256"],
        "suite_sha256": SUITE_SHA256,
        "scorer_version": SCORER_VERSION,
        "scorer_sha256": source_hash(("evaluation/scoring.py", "evaluation/coding.py")),
        "policy_sha256": source_hash(("intelligence/policy.py",)),
    }


def identity(repo: Path, config_path: Path) -> dict:
    git = git_snapshot(repo)
    model, config = model_snapshot(config_path)
    return _identity_from(git, model, config)


def _run_id(now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    return f"local-ui-{now:%Y%m%dT%H%M%S_%fZ}-{secrets.token_hex(2)}"


def start_bundle(
    config_path: Path,
    output_root: Path,
    *,
    browser: str | None = None,
    network_state: str | None = None,
    now: datetime | None = None,
) -> Path:
    repo = repository_root()
    started = now or datetime.now(UTC)
    bundle = output_root / _run_id(started)
    bundle.mkdir(parents=True, exist_ok=False)
    (bundle / "regressions").mkdir()
    (bundle / "sessions").mkdir()
    (bundle / "screenshots").mkdir()
    git = git_snapshot(repo)
    model, config = model_snapshot(config_path)
    _write_json(bundle / "git.json", git, exclusive=True)
    _write_json(
        bundle / "environment.json",
        environment_snapshot(browser=browser, network_state=network_state),
        exclusive=True,
    )
    _write_json(bundle / "model.json", model, exclusive=True)
    state = {
        "schema_version": 1,
        "run_id": bundle.name,
        "started_at": started.isoformat(),
        "repository_root": str(repo),
        "config_path": str(config_path.expanduser().resolve()),
        "config": config,
        "identity": _identity_from(git, model, config),
        "phases": {"regressions": False, "session": False, "finalized": False},
        "status": "INCOMPLETE",
    }
    _write_json(bundle / "state.json", state, exclusive=True)
    (bundle / "screenshots" / "CHECKLIST.md").write_text(
        "# Screenshot checklist\n\n- [ ] Ready / LOCAL MODEL / model metadata\n"
        "- [ ] Conversation / recall\n- [ ] Reset / post-reset\n- [ ] Error\n",
        encoding="utf-8", newline="\n",
    )
    return bundle


def ensure_fresh(bundle: Path) -> tuple[dict, Path, Path]:
    state = _json(bundle / "state.json")
    repo = Path(state["repository_root"])
    config = Path(state["config_path"])
    current = identity(repo, config)
    if current != state["identity"]:
        state["status"] = "INCOMPLETE"
        state["stale"] = {"expected": state["identity"], "current": current}
        _write_json(bundle / "state.json", state)
        raise GateError("bundle identity is stale; HEAD/config/model/suite/scorer/policy changed")
    return state, repo, config


def run_regressions(bundle: Path, *, offline_attested: bool, mock: bool = False) -> None:
    state, repo, config = ensure_fresh(bundle)
    outputs = bundle / "regressions"
    expected = [outputs / "v1.json", outputs / "v2.json", outputs / "v2-comparison.json"]
    if any(path.exists() for path in expected):
        raise GateError("regression evidence already exists; it will not be overwritten")
    try:
        v1 = run_v1(str(config), expected[0], offline_attested=offline_attested)
        if mock:
            v2 = run_mock(expected[1])
            comparison = compare(v2, v2)
        else:
            from .evaluation.real import run_real

            v2 = run_real(str(config), expected[1], offline_attested=offline_attested)
            baseline = _json(repo / "evidence/v2/raw/v2-real-1.json")
            comparison = compare(baseline, v2)
        _write_json(expected[2], comparison, exclusive=True)
    except Exception as exc:
        if (outputs / "failure.json").exists():
            raise GateError("a prior regression failure is already preserved") from exc
        _write_json(
            outputs / "failure.json",
            {"type": type(exc).__name__, "message": str(exc)},
            exclusive=True,
        )
        raise
    state["phases"]["regressions"] = True
    state["regression_summary"] = {
        "measurement_kind": v2["measurement_kind"],
        "v1_startup_success": v1["startup_success"],
        "v1_failure_count": v1["failure_count"],
        "v2_scoring_failures": v2.get("model_failures"),
        "v2_scoring_failure_tasks": [
            case["task_id"] for case in v2["cases"] if case.get("model_passed") is False
        ],
        "v2_runtime_failures": v2.get("runtime_failure_count"),
        "comparison_compatible": comparison.get("compatible"),
        "controlled_comparison": comparison.get("controlled_comparison"),
        "regressions": comparison.get("regressions"),
    }
    _write_json(bundle / "state.json", state)


def _parse_session(path: Path) -> list[dict]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeError, ValueError) as exc:
        raise GateError(f"invalid UTF-8 JSONL session {path.name}: {exc}") from exc
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise GateError(f"empty or invalid session {path.name}")
    return rows


def validate_reset_session(path: Path, started_at: datetime) -> dict[str, object]:
    rows = _parse_session(path)
    timestamps = []
    for row in rows:
        try:
            timestamps.append(datetime.fromisoformat(row["timestamp"]).astimezone(UTC))
        except (KeyError, TypeError, ValueError) as exc:
            raise GateError(f"invalid session timestamp in {path.name}") from exc
    now = datetime.now(UTC) + timedelta(minutes=5)
    in_window = min(timestamps) >= started_at.astimezone(UTC) and max(timestamps) <= now
    roles = [row.get("role") for row in rows]
    contents = [str(row.get("content", "")) for row in rows]
    starts = any(r == "event" and c == "Local UI V2 session started"
                 for r, c in zip(roles, contents, strict=True))
    reset_positions = [i for i, (r, c) in enumerate(zip(roles, contents, strict=True))
                       if r == "event" and c == RESET_EVENT]
    setup_positions = [
        i for i, (role, content) in enumerate(zip(roles, contents, strict=True))
        if role == "user" and "合言葉" in content and "青いりんご" in content
    ]
    recall_positions = [
        i for i, (role, content) in enumerate(zip(roles, contents, strict=True))
        if role == "user" and "合言葉" in content and "青いりんご" not in content
    ]
    recall = any(
        setup < question < len(rows) - 1
        and roles[setup + 1] == "assistant"
        and roles[question + 1] == "assistant"
        and "青いりんご" in contents[question + 1]
        for setup in setup_positions
        for question in recall_positions
    )
    post_reset = False
    for reset in reset_positions:
        tail = rows[reset + 1:]
        post_reset = post_reset or (
            any(row.get("role") == "user" for row in tail)
            and any(row.get("role") == "assistant" for row in tail)
        )
    return {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": _sha(path),
        "row_count": len(rows),
        "in_run_window": in_window,
        "start_event": starts,
        "recall_sequence": recall,
        "reset_event": bool(reset_positions),
        "post_reset_turn": post_reset,
        "valid": bool(in_window and starts and recall and reset_positions and post_reset),
        "first_timestamp": min(timestamps).isoformat(),
        "last_timestamp": max(timestamps).isoformat(),
    }


def session_candidates(bundle: Path, logs: Path) -> list[dict]:
    state, _, _ = ensure_fresh(bundle)
    started = datetime.fromisoformat(state["started_at"])
    candidates = []
    for path in sorted(logs.glob("*.jsonl")):
        try:
            candidates.append(validate_reset_session(path, started))
        except GateError as exc:
            candidates.append({"filename": path.name, "valid": False, "error": str(exc)})
    return candidates


def collect_session(bundle: Path, logs: Path, selected: Path | None) -> list[dict]:
    state, _, _ = ensure_fresh(bundle)
    candidates = session_candidates(bundle, logs)
    _write_json(bundle / "session-candidates.json", candidates)
    if selected is None:
        return candidates
    source = selected.expanduser().resolve()
    try:
        source.relative_to(logs.expanduser().resolve())
    except ValueError as exc:
        raise GateError("selected session must be inside the declared logs directory") from exc
    review = validate_reset_session(source, datetime.fromisoformat(state["started_at"]))
    if not review["valid"]:
        raise GateError("selected session does not satisfy the reset evidence contract")
    destination = bundle / "sessions" / source.name
    with source.open("rb") as incoming, destination.open("xb") as outgoing:
        shutil.copyfileobj(incoming, outgoing)
    _write_json(bundle / "sessions" / f"{source.name}.review.json", review, exclusive=True)
    state["phases"]["session"] = True
    state["session"] = review
    _write_json(bundle / "state.json", state)
    return candidates


def image_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data.startswith(b"\xff\xd8"):
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            if marker in {0xD8, 0xD9}:
                continue
            length = int.from_bytes(data[index:index + 2], "big")
            if marker in range(0xC0, 0xC4):
                return (
                    int.from_bytes(data[index + 5:index + 7], "big"),
                    int.from_bytes(data[index + 3:index + 5], "big"),
                )
            index += length
    raise GateError(f"unsupported or invalid PNG/JPEG screenshot: {path.name}")


def _attest(non_interactive: bool, supplied: set[str]) -> dict[str, bool]:
    unknown = supplied - ATTESTATIONS.keys()
    if unknown:
        raise GateError(f"unknown attestation(s): {', '.join(sorted(unknown))}")
    if non_interactive:
        return {key: key in supplied for key in ATTESTATIONS}
    answers = {}
    for key, prompt in ATTESTATIONS.items():
        answers[key] = input(f"{prompt} [y/N] ").strip().lower() in {"y", "yes"}
    return answers


def _copy_screenshots(bundle: Path, specs: list[str], existing: list[dict]) -> list[dict]:
    entries = list(existing)
    copied = {entry["sha256"]: entry["filename"] for entry in existing}
    for spec in specs:
        if "=" not in spec:
            raise GateError("screenshot must be KIND=PATH")
        kind, raw_path = spec.split("=", 1)
        if kind not in SCREENSHOT_KINDS:
            raise GateError(f"screenshot kind must be one of {sorted(SCREENSHOT_KINDS)}")
        source = Path(raw_path).expanduser().resolve()
        digest = _sha(source)
        if digest not in copied:
            destination = bundle / "screenshots" / source.name
            if destination.exists():
                raise GateError(f"screenshot filename already exists: {source.name}")
            with source.open("rb") as incoming, destination.open("xb") as outgoing:
                shutil.copyfileobj(incoming, outgoing)
            copied[digest] = destination.name
        width, height = image_dimensions(source)
        entries.append({
            "kind": kind, "filename": copied[digest], "bytes": source.stat().st_size,
            "sha256": digest, "width": width, "height": height,
        })
    return entries


def _regressions_pass(bundle: Path) -> bool:
    try:
        state = _json(bundle / "state.json")
        v1 = _json(bundle / "regressions/v1.json")
        v2 = _json(bundle / "regressions/v2.json")
        comparison = _json(bundle / "regressions/v2-comparison.json")
        failures = [case["task_id"] for case in v2["cases"] if not case["model_passed"]]
        return bool(
            v1["startup_success"] and v1["failure_count"] == 0
            and v1["model_file"]["sha256"] == state["identity"]["model_sha256"]
            and v2["measurement_kind"] == "real"
            and v2["model_identity"]["weights_sha256"] == state["identity"]["model_sha256"]
            and v2["runtime_failure_count"] == 0
            and failures == ["math-02"]
            and comparison["compatible"] and comparison["controlled_comparison"]
            and not comparison["regression_detected"]
        )
    except (OSError, KeyError, TypeError, ValueError):
        return False


def _manifest(bundle: Path) -> None:
    lines = []
    for path in sorted(p for p in bundle.rglob("*") if p.is_file()):
        if path.name == "manifest.sha256":
            continue
        lines.append(f"{_sha(path)}  {path.relative_to(bundle).as_posix()}  {path.stat().st_size}")
    (bundle / "manifest.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def finalize(
    bundle: Path,
    *,
    screenshots: list[str],
    supplied_attestations: set[str],
    non_interactive: bool,
) -> str:
    state, _, _ = ensure_fresh(bundle)
    screenshot_path = bundle / "screenshots.json"
    screenshot_rows = _json(screenshot_path) if screenshot_path.exists() else []
    if screenshots:
        screenshot_rows = _copy_screenshots(bundle, screenshots, screenshot_rows)
        _write_json(screenshot_path, screenshot_rows)
    attestations = _attest(non_interactive, supplied_attestations)
    _write_json(
        bundle / "human-attestations.json",
        {"source": "interactive" if not non_interactive else "explicit-cli-flags",
         "answers": attestations},
    )
    kinds = {row["kind"] for row in screenshot_rows}
    clean_source = not state["identity"]["tracked_status"]
    ready = bool(
        _regressions_pass(bundle)
        and state["phases"]["session"]
        and SCREENSHOT_KINDS <= kinds
        and all(attestations.values())
        and clean_source
    )
    status = "READY_FOR_REVIEW" if ready else "INCOMPLETE"
    missing = []
    if not _regressions_pass(bundle):
        missing.append("reviewable real V1/V2/comparison regression evidence")
    if not state["phases"]["session"]:
        missing.append("validated reset session")
    if SCREENSHOT_KINDS - kinds:
        missing.append("screenshots: " + ", ".join(sorted(SCREENSHOT_KINDS - kinds)))
    if not clean_source:
        missing.append("clean tracked Git source state")
    missing.extend(f"human attestation: {key}" for key, value in attestations.items() if not value)
    git = _json(bundle / "git.json")
    environment = _json(bundle / "environment.json")
    model = _json(bundle / "model.json")
    report = [
        "# ARK Target-PC Report", "", f"- Run ID: `{state['run_id']}`",
        "- Branch / HEAD: "
        f"`{git.get('branch')}` / `{state['identity']['head']}`",
        f"- Git status: `{json.dumps(git['status'], ensure_ascii=False)}`",
        f"- Overall: **{status}**", "- OFFICIAL PASS: **NOT DECLARED**", "",
        "## Evidence", "", f"- Model SHA-256: `{state['identity']['model_sha256']}`",
        f"- Model: `{model.get('filename')}` / `{model.get('quantization')}` / "
        f"`{model.get('bytes')}` bytes",
        f"- Config SHA-256: `{state['identity']['config_sha256']}`",
        f"- V2 suite SHA-256: `{state['identity']['suite_sha256']}`",
        f"- Environment: `{json.dumps(environment, ensure_ascii=False)}`",
        "- Regression summary: "
        f"`{json.dumps(state.get('regression_summary'), ensure_ascii=False)}`",
        f"- Session: `{json.dumps(state.get('session'), ensure_ascii=False)}`",
        f"- Screenshot kinds: `{', '.join(sorted(kinds)) or 'none'}`", "",
        "## Human attestations", "",
    ]
    report.extend(f"- {key}: {value}" for key, value in attestations.items())
    report.extend(["", "## Missing evidence", ""])
    report.extend(f"- {item}" for item in missing or ["None before independent review"])
    report.extend(["", "This collector never declares OFFICIAL PASS, uploads or merges.\n"])
    (bundle / "TARGET_PC_REPORT.md").write_text("\n".join(report), encoding="utf-8", newline="\n")
    state["phases"]["finalized"] = True
    state["status"] = status
    state["missing"] = missing
    _write_json(bundle / "state.json", state)
    _manifest(bundle)
    return status


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ARK target-PC evidence collector")
    sub = parser.add_subparsers(dest="gate", required=True)
    local = sub.add_parser("local-ui", help="Local UI target-PC gate")
    action = local.add_mutually_exclusive_group(required=True)
    action.add_argument("--start", action="store_true")
    action.add_argument("--regressions", action="store_true")
    action.add_argument("--collect-sessions", action="store_true")
    action.add_argument("--finalize", action="store_true")
    local.add_argument("--bundle", type=Path)
    local.add_argument("--config", type=Path, default=Path("config.toml"))
    local.add_argument("--output-root", type=Path, default=Path("evidence-bundles"))
    local.add_argument("--browser")
    local.add_argument("--network-state")
    local.add_argument("--offline-attested", action="store_true")
    local.add_argument("--mock", action="store_true", help="CI plumbing only; never review-ready")
    local.add_argument("--logs", type=Path, default=Path("logs"))
    local.add_argument("--session", type=Path)
    local.add_argument("--screenshot", action="append", default=[])
    local.add_argument("--attest", action="append", choices=tuple(ATTESTATIONS), default=[])
    local.add_argument("--non-interactive", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.start:
            bundle = start_bundle(
                args.config, args.output_root, browser=args.browser,
                network_state=args.network_state,
            )
            print(f"Gate started: {bundle}\nStatus: INCOMPLETE")
            return 0
        if args.bundle is None:
            parser.error("--bundle is required after --start")
        if args.regressions:
            run_regressions(args.bundle, offline_attested=args.offline_attested, mock=args.mock)
            print(f"Regression originals saved without overwrite: {args.bundle}")
            return 0
        if args.collect_sessions:
            candidates = collect_session(args.bundle, args.logs, args.session)
            print(json.dumps(candidates, ensure_ascii=False, indent=2))
            if args.session is None:
                print("No session copied. Review candidates, then pass --session explicitly.")
            return 0
        status = finalize(
            args.bundle, screenshots=args.screenshot,
            supplied_attestations=set(args.attest), non_interactive=args.non_interactive,
        )
        print(f"Bundle finalized: {args.bundle}\nStatus: {status}\nOFFICIAL PASS not declared.")
        return 0 if status == "READY_FOR_REVIEW" else 2
    except (GateError, OSError, ValueError) as exc:
        print(f"ARK gate error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
