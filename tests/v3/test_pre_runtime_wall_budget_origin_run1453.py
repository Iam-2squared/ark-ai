"""Run1453: one approved wall-time epoch spans CLI runtime identity and backend work.

Synthetic clocks and fake identity/local checks only. No torch, GPU, preflight,
training, Candidate creation, or external compute is reached.
"""

from argparse import Namespace
from pathlib import Path

import pytest

from ark.learning import hf_lora, preflight, runtime_guard, training_cli


def _args(tmp_path: Path, command: str) -> Namespace:
    common = {
        "snapshot": tmp_path / "snapshot.json",
        "base_dir": tmp_path / "base",
        "dataset": tmp_path / "dataset.json",
        "provenance": tmp_path / "provenance.json",
        "contamination": tmp_path / "contamination.json",
        "probe": tmp_path / "probe.txt",
        "code_root": tmp_path / "code",
        "code_sha": "0" * 40,
    }
    if command == "preflight":
        return Namespace(**common, report=tmp_path / "report.json")
    return Namespace(
        **common,
        preflight_report=tmp_path / "preflight-report.json",
        output_dir=tmp_path / "candidate-output",
    )


@pytest.mark.parametrize(
    ("command", "phase"),
    (
        ("preflight", "preflight-local-identity"),
        ("training", "training-local-identity"),
    ),
)
def test_cli_and_runtime_share_one_wall_budget_epoch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    phase: str,
) -> None:
    now = [100.0]
    monkeypatch.setattr(runtime_guard.time, "monotonic", lambda: now[0])
    snapshot = {"budget": {"wall_clock_timeout_minutes": 1}}

    monkeypatch.setattr(training_cli, "load_snapshot", lambda _path: snapshot)
    monkeypatch.setattr(
        training_cli, "validate_experiment_001", lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        preflight, "validate_experiment_001", lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        hf_lora, "validate_experiment_001", lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        training_cli, "_verify_common_evidence", lambda *_args, **_kwargs: None,
    )

    def slow_runtime_identity(_snapshot: dict) -> object:
        now[0] += 30.0
        return object()

    def slow_local_identity(*_args: object, **_kwargs: object) -> tuple[list, list]:
        now[0] += 31.0
        return [], []

    monkeypatch.setattr(
        training_cli, "_verify_actual_runtime", slow_runtime_identity,
    )
    monkeypatch.setattr(hf_lora, "_verify_local_identities", slow_local_identity)
    monkeypatch.setattr(
        hf_lora,
        "_build_model_and_tokenizer",
        lambda *_args, **_kwargs: pytest.fail("model loading must remain unreachable"),
    )

    if command == "preflight":
        monkeypatch.setattr(
            training_cli, "_validate_new_preflight_report_path", lambda path: path,
        )
        with pytest.raises(
            RuntimeError,
            match=f"timeout exceeded during {phase}",
        ):
            training_cli.run_preflight(_args(tmp_path, command))
    else:
        monkeypatch.setattr(
            training_cli, "_verify_preflight_report", lambda *_args, **_kwargs: None,
        )
        monkeypatch.setattr(
            hf_lora, "_validate_candidate_output_path", lambda *_args: None,
        )
        with pytest.raises(
            RuntimeError,
            match=f"timeout exceeded during {phase}",
        ):
            training_cli.run_training(_args(tmp_path, command))
