"""Disposable WAL diagnostic must reject aliased sidecars before readback."""

import os
import runpy
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def oracle() -> dict[str, object]:
    script = Path(__file__).resolve().parents[1] / "scripts"
    return runpy.run_path(str(script / "diagnose_revocation_wal_processes.py"))


@pytest.fixture
def synthetic_db(tmp_path: Path, oracle: dict[str, object]) -> Path:
    path = tmp_path / "revocation.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute(oracle["_EXPECTED_DDL"])
        conn.execute("PRAGMA user_version=1")
        conn.execute(
            "INSERT INTO synthetic_context_revocations VALUES(?,?)",
            (oracle["_SCOPE_DIGEST"], 2000),
        )
    return path


def test_canonical_single_link_readback_is_accepted(
    oracle: dict[str, object], synthetic_db: Path,
) -> None:
    assert oracle["_verify_row"](synthetic_db) is True


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
@pytest.mark.parametrize("alias", ["symlink", "directory", "hardlink"])
def test_untrusted_sidecar_refused_before_sqlite_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    oracle: dict[str, object], synthetic_db: Path,
    suffix: str, alias: str,
) -> None:
    sidecar = synthetic_db.with_name(synthetic_db.name + suffix)
    if alias == "directory":
        sidecar.mkdir()
    else:
        target = tmp_path / ("target" + suffix)
        target.write_bytes(b"synthetic, not a SQLite sidecar")
        try:
            if alias == "symlink":
                sidecar.symlink_to(target)
            else:
                os.link(target, sidecar)
        except (NotImplementedError, OSError) as exc:
            pytest.skip(f"sidecar alias creation unavailable: {type(exc).__name__}")

    def unexpected_sqlite(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("unsafe sidecar should be rejected before SQLite open")

    monkeypatch.setattr(sqlite3, "connect", unexpected_sqlite)
    assert oracle["_verify_row"](synthetic_db) is False
