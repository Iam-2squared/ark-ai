"""Invalid preflight output paths must fail before local runtime initialization."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.learning.training_cli as cli


@pytest.mark.parametrize("path_kind", ("existing", "missing_parent"))
def test_invalid_report_destination_is_rejected_before_runtime_probe(
    tmp_path, monkeypatch, path_kind,
):
    if path_kind == "existing":
        report = tmp_path / "already-exists.json"
        report.write_text("preserve", encoding="utf-8")
    else:
        report = tmp_path / "missing-parent" / "report.json"

    args = SimpleNamespace(
        snapshot=tmp_path / "snapshot.json",
        provenance=tmp_path / "provenance.json",
        contamination=tmp_path / "contamination.json",
        code_root=tmp_path,
        code_sha="a" * 40,
        report=report,
        base_dir=tmp_path / "base",
        dataset=tmp_path / "dataset.json",
        probe=tmp_path / "probe.json",
    )
    monkeypatch.setattr(cli, "load_snapshot", lambda _path: {})
    monkeypatch.setattr(cli, "validate_experiment_001", lambda *_a, **_k: "snapshot")
    monkeypatch.setattr(cli, "_verify_common_evidence", lambda *_a, **_k: None)
    runtime_calls = []

    def forbidden_runtime_probe(*_args, **_kwargs):
        runtime_calls.append(True)
        raise AssertionError("invalid output must not initialize torch or a local accelerator")

    monkeypatch.setattr(cli, "_verify_actual_runtime", forbidden_runtime_probe)
    with pytest.raises(
        RuntimeError,
        match="preflight report path must be a new file under an existing directory",
    ):
        cli.run_preflight(args)

    assert runtime_calls == []
    if path_kind == "existing":
        assert report.read_text(encoding="utf-8") == "preserve"
    else:
        assert not report.parent.exists()
