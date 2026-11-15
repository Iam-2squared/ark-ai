"""Run906: retained, non-authorizing SQLite sidecar seal digest ingress.

No store, SQLite connection, private path bytes or sidecar content is opened.
This is a bounded synthetic metadata check, not provenance/transaction proof.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark import disconnected_sqlite_sidecar_custody as mod

_SUFFIXES = ("-wal", "-shm", "-journal")


def _seal():
    return mod.DetachedSQLiteSidecarSeal(
        "a" * 64, "b" * 64, "c" * 64,
        tuple(mod.DetachedSQLiteSidecarState(suffix, False, None) for suffix in _SUFFIXES),
        "d" * 64,
    )


def test_retained_digest_shape_accepts_bounded_inert_metadata():
    seal = _seal()
    view = mod._seal_snapshot(seal)
    assert view[:4] == (
        seal.path_sha256, seal.directories_sha256,
        seal.main_identity_sha256, seal.fingerprint,
    )
    assert tuple(item[1] for item in view[4]) == (False, False, False)
    assert seal.sqlite_transaction_atomicity_proven is False
    assert seal.tool_execution_authorized is False


@pytest.mark.parametrize("field", (
    "path_sha256", "directories_sha256", "main_identity_sha256", "fingerprint",
))
def test_oversized_retained_header_denied_before_any_sidecar_probe(
    monkeypatch, tmp_path, field,
):
    calls = []

    def forbidden(_path):
        calls.append("filesystem")
        raise AssertionError("unbounded digest reached sidecar inventory")

    seal = replace(_seal(), **{field: "a" * 100_000})
    with monkeypatch.context() as patch:
        patch.setattr(mod, "_capture_once", forbidden)
        with pytest.raises(mod.SQLiteSidecarCustodyRejected, match="malformed retained"):
            mod.review_disconnected_sqlite_sidecars(tmp_path / "absent.sqlite", seal)
    assert calls == []


@pytest.mark.parametrize("position", range(3))
def test_oversized_retained_sidecar_digest_denied_before_probe(
    monkeypatch, tmp_path, position,
):
    seal = _seal()
    rows = list(seal.sidecars)
    rows[position] = mod.DetachedSQLiteSidecarState(
        _SUFFIXES[position], True, "a" * 100_000,
    )
    seal = replace(seal, sidecars=tuple(rows))
    calls = []

    with monkeypatch.context() as patch:
        patch.setattr(mod, "_capture_once", lambda _path: calls.append("probe"))
        with pytest.raises(mod.SQLiteSidecarCustodyRejected, match="malformed retained"):
            mod.review_disconnected_sqlite_sidecars(tmp_path / "absent.sqlite", seal)
    assert calls == []


def test_retained_digest_must_be_exact_string_not_string_subclass():
    class Deceptive(str):
        pass

    seal = replace(_seal(), fingerprint=Deceptive("d" * 64))
    with pytest.raises(mod.SQLiteSidecarCustodyRejected, match="malformed retained"):
        mod._seal_snapshot(seal)
