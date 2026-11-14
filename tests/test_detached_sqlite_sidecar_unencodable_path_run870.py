"""Private detached SQLite fixture paths fail closed before filesystem access.

POSIX-only synthetic encoding errors; no database contents or live effects.
"""
from __future__ import annotations

import os

import pytest

from ark import disconnected_sqlite_sidecar_custody as custody


@pytest.mark.parametrize("operation", ("capture", "review"))
def test_invalid_native_path_encoding_is_a_typed_denial(tmp_path, operation):
    if os.name != "posix":
        pytest.skip("POSIX native encoding rejection fixture")
    path = tmp_path / ("invalid_" + "\ud800" + ".sqlite")
    try:
        os.fsencode(path)
    except UnicodeError:
        pass
    else:
        pytest.skip("host accepts the fixture's native path encoding")

    def review():
        if operation == "capture":
            return custody.capture_disconnected_sqlite_sidecars(path)
        return custody.review_disconnected_sqlite_sidecars(path, object())

    with pytest.raises(
        custody.SQLiteSidecarCustodyRejected, match="path encoding unavailable",
    ) as rejected:
        review()
    assert "invalid_" not in str(rejected.value)
