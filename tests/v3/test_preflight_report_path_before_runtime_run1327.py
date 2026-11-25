"""Run1327: invalid preflight report destinations fail before evidence I/O/runtime probes."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from ark.learning import training_cli as cli


def test_invalid_report_path_is_rejected_before_common_evidence_or_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = {"synthetic": "authorized-shape-placeholder"}
    validated: list[tuple[object, str]] = []

    monkeypatch.setattr(cli, "load_snapshot", lambda _path: snapshot)

    def validate(value: object, *, authorization_scope: str) -> None:
        validated.append((value, authorization_scope))

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("invalid report path must stop before evidence/runtime work")

    monkeypatch.setattr(cli, "validate_experiment_001", validate)
    monkeypatch.setattr(cli, "_verify_common_evidence", forbidden)
    monkeypatch.setattr(cli, "_verify_actual_runtime", forbidden)

    args = argparse.Namespace(
        snapshot=tmp_path / "snapshot.json",
        report=tmp_path / "nested" / ".." / "report.json",
        provenance=tmp_path / "provenance.json",
        contamination=tmp_path / "contamination.json",
        code_root=tmp_path,
        code_sha="0" * 40,
        base_dir=tmp_path,
        dataset=tmp_path / "dataset.jsonl",
        probe=tmp_path / "probe.json",
    )

    with pytest.raises(RuntimeError, match="accepted local path"):
        cli.run_preflight(args)

    assert validated == [(snapshot, "preflight")]
