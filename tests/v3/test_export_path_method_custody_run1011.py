"""Run1011: exact local path inspection dependency custody."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.learning.export_plan import _validate_export_output_path


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    base = tmp_path / "base-model"
    candidate = tmp_path / "merged-candidate"
    base.mkdir()
    candidate.mkdir()
    return base, candidate, tmp_path / "export"


def _check(output: Path, base: Path, candidate: Path) -> None:
    _validate_export_output_path(
        output,
        base_dir=base,
        merged_candidate_dir=candidate,
        current_model_path=None,
    )


@pytest.mark.parametrize(
    "member",
    ("__fspath__", "absolute", "lstat", "is_dir", "resolve"),
)
def test_export_rejects_path_method_rebinding_before_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, member: str,
) -> None:
    base, candidate, output = _roots(tmp_path)
    calls: list[str] = []
    path_type = type(Path("."))

    def forbidden(*args, **kwargs):
        calls.append(member)
        raise AssertionError("replaced pathlib method executed before admission")

    monkeypatch.setattr(path_type, member, forbidden)
    with pytest.raises(ValueError, match="path inspection dependencies changed"):
        _check(output, base, candidate)
    assert calls == []


@pytest.mark.parametrize(
    ("target", "member"),
    [
        ("os", "fsencode"),
        ("os", "fspath"),
        ("os", "lstat"),
        ("os", "stat"),
        ("os", "getcwd"),
        ("os.path", "abspath"),
        ("os.path", "join"),
        ("os.path", "realpath"),
    ],
)
def test_export_rejects_os_path_dependency_rebinding_before_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str, member: str,
) -> None:
    base, candidate, output = _roots(tmp_path)
    calls: list[str] = []

    def forbidden(*args, **kwargs):
        calls.append(member)
        raise AssertionError("replaced os path dependency executed before admission")

    owner = os.path if target == "os.path" else os
    monkeypatch.setattr(owner, member, forbidden)
    with pytest.raises(ValueError, match="path inspection dependencies changed"):
        _check(output, base, candidate)
    assert calls == []
