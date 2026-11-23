"""Run1133: execution snapshot pins the descriptor-stat primitive."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.learning import execution as mod


def test_live_fstat_substitution_is_denied_by_policy_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def forbidden(fd: int):
        calls.append(fd)
        raise AssertionError("substituted fstat must not execute")

    monkeypatch.setattr(mod.os, "fstat", forbidden)
    with pytest.raises(
        ValueError,
        match="execution snapshot stat policy changed",
    ):
        mod._require_original_stat_policy()

    assert calls == []


def test_captured_fstat_substitution_is_denied_before_file_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "snapshot.json"
    source.write_text('{"authorization":false}', encoding="utf-8")
    calls: list[int] = []
    open_calls: list[Path] = []

    def forbidden(fd: int):
        calls.append(fd)
        raise AssertionError("substituted fstat must not execute")

    def forbidden_open(self: Path, *args, **kwargs):
        open_calls.append(self)
        raise AssertionError("snapshot must be rejected before file open")

    monkeypatch.setattr(mod, "_ORIGINAL_FSTAT", forbidden)
    monkeypatch.setattr(Path, "open", forbidden_open)
    with pytest.raises(
        ValueError,
        match="execution snapshot stat policy changed",
    ):
        mod.load_snapshot(source)

    assert calls == []
    assert open_calls == []


def test_reentrant_open_cannot_replace_fstat_before_descriptor_inspection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "snapshot.json"
    source.write_text('{"authorization":false}', encoding="utf-8")
    original_open = Path.open
    calls: list[int] = []

    def forbidden(fd: int):
        calls.append(fd)
        raise AssertionError("substituted fstat must not execute")

    def switched_open(self: Path, *args, **kwargs):
        handle = original_open(self, *args, **kwargs)
        if self == source:
            monkeypatch.setattr(mod, "_ORIGINAL_FSTAT", forbidden)
        return handle

    monkeypatch.setattr(Path, "open", switched_open)
    with pytest.raises(
        ValueError,
        match="execution snapshot stat policy changed",
    ):
        mod.load_snapshot(source)

    assert calls == []
