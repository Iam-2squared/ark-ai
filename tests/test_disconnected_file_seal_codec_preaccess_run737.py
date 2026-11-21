"""Fail closed before detached synthetic file bytes reach substituted digest code.

No real user file, mutation, SQLite connection, or tool authority is involved.
"""

from __future__ import annotations

import re

import pytest

from ark import disconnected_file_seal as module


def _source(tmp_path):
    path = tmp_path / "detached-synthetic-file.db"
    path.write_bytes(b"synthetic-private-seal-bytes-not-for-disclosure")
    return path


def _replace_codec(monkeypatch, dependency):
    def unsafe(*_args, **_kwargs):
        pytest.fail("unreviewed digest callback received file metadata or bytes")

    if dependency == "hashlib_module":
        monkeypatch.setattr(module, "hashlib", object())
    elif dependency == "sha256":
        monkeypatch.setattr(module.hashlib, "sha256", unsafe)
    elif dependency == "domain":
        monkeypatch.setattr(module, "_DOMAIN", b"unreviewed-seal-domain\\0")
    elif dependency == "sha_pattern":
        monkeypatch.setattr(module, "_SHA", re.compile(".*"))
    elif dependency == "read_budget":
        monkeypatch.setattr(module, "_MAX_BYTES", 9 * 1024 * 1024)
    elif dependency == "path_budget":
        monkeypatch.setattr(module, "_MAX_PATH", 5000)
    else:
        pytest.fail("unrecognized synthetic dependency")


@pytest.mark.parametrize("dependency", (
    "hashlib_module", "sha256", "domain", "sha_pattern",
    "read_budget", "path_budget",
))
def test_capture_rejects_mutable_digest_and_budget_before_file_read(
    tmp_path, monkeypatch, dependency,
):
    path = _source(tmp_path)
    original = path.read_bytes()
    _replace_codec(monkeypatch, dependency)
    with pytest.raises(module.DisconnectedFileSealRejected, match="digest or custody budget"):
        module.capture_disconnected_file_seal(path)
    assert path.read_bytes() == original


@pytest.mark.parametrize("dependency", (
    "hashlib_module", "sha256", "domain", "sha_pattern",
    "read_budget", "path_budget",
))
def test_review_rejects_mutable_digest_and_budget_before_file_read(
    tmp_path, monkeypatch, dependency,
):
    path = _source(tmp_path)
    retained = module.capture_disconnected_file_seal(path)
    original = path.read_bytes()
    _replace_codec(monkeypatch, dependency)
    with pytest.raises(module.DisconnectedFileSealRejected, match="digest or custody budget"):
        module.review_disconnected_file_seal(path, retained)
    assert path.read_bytes() == original


def test_unmodified_local_seal_stays_non_authorizing(tmp_path):
    path = _source(tmp_path)
    retained = module.capture_disconnected_file_seal(path)
    observed = module.review_disconnected_file_seal(path, retained)
    assert observed == retained
    assert observed.source_authenticated is False
    assert observed.wal_snapshot_verified is False
    assert observed.file_mutation_authorized is False
