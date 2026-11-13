"""Reject malformed detached SQLite names before any descriptor inventory.

The exact local Path admission is a lexical preflight only. These fixtures
never open a user database, prove future custody, or authorize any effect.
"""

from pathlib import Path

import pytest

from ark import disconnected_sqlite_sidecar_custody as custody


@pytest.mark.parametrize(
    "source",
    (
        Path("/synthetic/fixture\x00.sqlite3"),
        Path("/synthetic\x00/fixture.sqlite3"),
        # Main pathname is under 4096, but the -journal sidecar exceeds it.
        Path("/" + "x" * (4096 - len("-journal"))),
        # Even the main pathname alone is beyond the local lexical budget.
        Path("/" + "y" * 4096),
    ),
)
def test_reject_nul_and_sidecar_budget_before_descriptor_inventory(
    monkeypatch: pytest.MonkeyPatch, source: Path,
) -> None:
    inspected: list[Path] = []

    def forbidden_inventory(path: Path) -> object:
        inspected.append(path)
        raise AssertionError("malformed path reached descriptor inventory")

    monkeypatch.setattr(custody, "_capture_once", forbidden_inventory)
    with pytest.raises(
        custody.SQLiteSidecarCustodyRejected,
        match="exact absolute fixture database Path required",
    ):
        custody.capture_disconnected_sqlite_sidecars(source)
    assert inspected == []
