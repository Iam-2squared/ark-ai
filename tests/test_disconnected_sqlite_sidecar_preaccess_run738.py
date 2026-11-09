"""Synthetic pre-access guards for detached SQLite pathname/sidecar metadata.

No real database, retained authority, OS dispatch, consent, or actual SQLite
row bytes are involved. Tamper probes must fail before reading fixture paths.
"""

from __future__ import annotations

import re

import pytest

from ark import disconnected_sqlite_sidecar_custody as module
from ark.disconnected_sqlite_sidecar_custody import (
    SQLiteSidecarCustodyRejected,
    capture_disconnected_sqlite_sidecars,
    review_disconnected_sqlite_sidecars,
)


@pytest.mark.parametrize(
    ("name", "changed"),
    [
        ("_DOMAIN", b"unexpected-domain"),
        ("_SHA", re.compile(r".*")),
        ("_SUFFIXES", ("-wal", "-journal")),
        ("_MAX_PATH", 8192),
        ("_MAX_PATH", True),
        ("_MAX_FILE_BYTES", 128 * 1024 * 1024),
        ("_MAX_FILE_BYTES", True),
        ("hashlib", object()),
        ("json", object()),
    ],
)
@pytest.mark.parametrize("operation", ("capture", "review"))
def test_detached_sqlite_codec_change_rejected_before_path_access(
    tmp_path, monkeypatch, name, changed, operation,
):
    path = tmp_path / "private-fixture.sqlite3"
    monkeypatch.setattr(module, name, changed)

    def must_not_open(_path):
        pytest.fail("codec modification reached detached filesystem inspection")

    monkeypatch.setattr(module, "_capture_once", must_not_open)
    with pytest.raises(SQLiteSidecarCustodyRejected, match="codec or inventory bounds"):
        if operation == "capture":
            capture_disconnected_sqlite_sidecars(path)
        else:
            review_disconnected_sqlite_sidecars(path, None)
    assert not path.exists()


@pytest.mark.parametrize("callback", ("sha256", "dumps"))
def test_detached_sqlite_digest_callback_replacement_not_invoked(
    monkeypatch, callback,
):
    calls = []

    def malicious(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("private path passed to substituted digest codec")

    target = module.hashlib if callback == "sha256" else module.json
    monkeypatch.setattr(target, callback, malicious)
    with pytest.raises(SQLiteSidecarCustodyRejected, match="codec or inventory bounds"):
        module._hash(("path", "/synthetic/private/secret.sqlite3"))
    assert calls == []
