"""Encoded POSIX path admission for detached, read-only SQLite inventory.

Synthetic names are rejected before touching any descriptor. These tests do
not authenticate a filesystem namespace or establish future path custody.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark import disconnected_sqlite_sidecar_custody as custody


@pytest.mark.parametrize(
    "source",
    (
        Path("/fixture/" + "界" * 1400 + ".sqlite3"),
        Path("/" + "é" * 2200 + "/fixture.sqlite3"),
    ),
)
def test_multibyte_path_budget_rejected_before_inventory(
    monkeypatch: pytest.MonkeyPatch, source: Path,
) -> None:
    assert len(str(source)) < 4096
    assert len(os.fsencode(source)) + len("-journal") > 4096
    inspected: list[Path] = []

    def forbidden_inventory(path: Path) -> object:
        inspected.append(path)
        raise AssertionError("oversized encoded source reached descriptor inventory")

    monkeypatch.setattr(custody, "_capture_once", forbidden_inventory)
    with pytest.raises(
        custody.SQLiteSidecarCustodyRejected,
        match="exact absolute fixture database Path required",
    ):
        custody.capture_disconnected_sqlite_sidecars(source)
    assert inspected == []


def test_small_encoded_path_keeps_exact_local_source() -> None:
    source = Path("/synthetic/fixture.sqlite3")
    assert custody._path(source) is source
