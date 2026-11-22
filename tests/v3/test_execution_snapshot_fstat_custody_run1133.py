"""Run1133: execution snapshot pins the descriptor-stat primitive."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.learning import execution as mod


@pytest.mark.parametrize("target", ("live os.fstat", "captured alias"))
def test_fstat_substitution_is_denied_before_descriptor_stat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    source = tmp_path / "snapshot.json"
    source.write_text('{"authorization":false}', encoding="utf-8")
    calls: list[int] = []

    def forbidden(fd: int):
        calls.append(fd)
        raise AssertionError("substituted fstat must not execute")

    if target == "live os.fstat":
        monkeypatch.setattr(mod.os, "fstat", forbidden)
    else:
        monkeypatch.setattr(mod, "_ORIGINAL_FSTAT", forbidden)

    with pytest.raises(
        ValueError,
        match="execution snapshot stat policy changed",
    ):
        mod.load_snapshot(source)

    assert calls == []


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
            monkeypatch.setattr(mod.os, "fstat", forbidden)
        return handle

    monkeypatch.setattr(Path, "open", switched_open)
    with pytest.raises(
        ValueError,
        match="execution snapshot stat policy changed",
    ):
        mod.load_snapshot(source)

    assert calls == []
