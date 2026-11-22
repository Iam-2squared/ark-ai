"""Run1132: platform identity is part of the V3 no-follow policy."""

from __future__ import annotations

import pytest

import ark.learning.identity as identity


@pytest.mark.parametrize(
    "target",
    ("live platform attribute", "captured platform alias"),
)
def test_replaced_platform_identity_is_denied_before_metadata_comparison(
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    original = identity._ORIGINAL_OS_NAME
    replacement = "nt" if original != "nt" else "posix"
    if target == "live platform attribute":
        monkeypatch.setattr(identity.os, "name", replacement)
    else:
        monkeypatch.setattr(identity, "_ORIGINAL_OS_NAME", replacement)

    entry_epoch = (1, 2, 0o040755, 4096, 100, 200, 1)
    path_epoch = (9, 8, 0o040755, 0, 5_000_100, 900, 2)

    with pytest.raises(
        ValueError,
        match="identity reparse-point policy changed",
    ):
        identity._entry_metadata_matches_path(
            entry_epoch,
            path_epoch,
            windows=True,
            is_dir=True,
        )
