"""Invalid preflight output paths must fail before local runtime initialization."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.learning.training_cli as cli


@pytest.mark.parametrize(
    "path_kind",
    ("existing", "missing_parent", "parent_symlink", "dangling_symlink", "parent_traversal", "oversized"),
)
def test_invalid_report_destination_is_rejected_before_runtime_probe(
    tmp_path, monkeypatch, path_kind,
):
    if path_kind == "existing":
        report = tmp_path / "already-exists.json"
        report.write_text("preserve", encoding="utf-8")
    elif path_kind == "missing_parent":
        report = tmp_path / "missing-parent" / "report.json"
    elif path_kind == "parent_symlink":
        real_parent = tmp_path / "real-parent"
        real_parent.mkdir()
        linked_parent = tmp_path / "linked-parent"
        try:
            linked_parent.symlink_to(real_parent, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"directory symlink unavailable: {exc}")
        report = linked_parent / "report.json"
    elif path_kind == "dangling_symlink":
        report = tmp_path / "dangling-report.json"
        try:
            report.symlink_to(tmp_path / "not-created.json")
        except OSError as exc:
            pytest.skip(f"file symlink unavailable: {exc}")
    elif path_kind == "parent_traversal":
        report = tmp_path / "missing" / ".." / "report.json"
    else:
        report = cli.Path("x" * 4097)

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
        match="preflight report path must be a new file under real non-symlink directories",
    ):
        cli.run_preflight(args)

    assert runtime_calls == []
    if path_kind == "existing":
        assert report.read_text(encoding="utf-8") == "preserve"
    else:
        assert not report.parent.exists()
