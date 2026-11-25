"""Run1351: reject report paths with a symlinked grandparent before open."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.learning import training_cli as cli


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_symlinked_grandparent_is_denied_before_open_and_preserves_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_root = tmp_path / "real"
    real_parent = real_root / "child"
    real_parent.mkdir(parents=True)
    sentinel = real_parent / "sentinel.bin"
    sentinel.write_bytes(b"preserve-existing-target")

    linked_root = tmp_path / "linked"
    try:
        linked_root.symlink_to(real_root, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation is not permitted")

    report = linked_root / "child" / "preflight.json"
    opened: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def forbidden_open(*args: object, **kwargs: object) -> int:
        opened.append((args, kwargs))
        raise AssertionError("nested reparse ancestor must be rejected before open")

    monkeypatch.setattr(cli.os, "open", forbidden_open)
    with pytest.raises(RuntimeError, match="non-reparse directory"):
        cli._write_new_preflight_report(report, b"synthetic-report")

    assert opened == []
    assert sentinel.read_bytes() == b"preserve-existing-target"
    assert not (real_parent / "preflight.json").exists()
