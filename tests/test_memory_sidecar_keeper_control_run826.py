"""Disposable WAL keeper control for independent-process Memory races.

The control never repairs a sidecar, retries a rejected open, touches a user
database or attributes a committed write. Both control and default mode use
owned temporary files and report no path/row/token bytes.
"""

from __future__ import annotations

import json
from importlib import util
from pathlib import Path

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore, deterministic_memory_id

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "diagnose_memory_sidecar_startup.py"
)


def _load():
    spec = util.spec_from_file_location("ark_disposable_wal_keeper_run826", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()


@pytest.mark.parametrize(
    ("operation", "identity", "expected"),
    (
        ("create", "same-identity", ("CONFLICT", "CREATED")),
        ("create", "separate-owner", ("CREATED", "CREATED")),
        ("generation-cas", "same-identity", ("CONFLICT", "UPDATED")),
        ("generation-cas", "separate-owner", ("UPDATED", "UPDATED")),
    ),
)
def test_keeper_preserves_true_two_process_cas_and_scoped_rows(
    tmp_path: Path,
    operation: str,
    identity: str,
    expected: tuple[str, str],
) -> None:
    path = tmp_path / "memory.sqlite"
    outcomes = _DIAG._probe(
        path, identity, "sequential", operation, wal_keeper=True,
    )
    assert len(outcomes) == 2
    assert tuple(sorted(result["status"] for result in outcomes)) == expected
    report = json.dumps(outcomes)
    for private in (str(tmp_path), "memory.sqlite", "owner-a", "owner-b", "source"):
        assert private not in report
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1001)
    scopes = [MemoryScope("owner-a", "fixture")]
    if identity == "separate-owner":
        scopes.append(MemoryScope("owner-b", "fixture"))
    for scope in scopes:
        row = store.get(deterministic_memory_id(scope, "source"), scope)
        assert row is not None
        assert row.revision == (2 if operation == "generation-cas" else 1)
        assert len(tuple(store.events(scope))) == row.revision


@pytest.mark.parametrize("operation", ("create", "generation-cas"))
def test_keeper_cli_is_path_free_and_explicit(
    capsys: pytest.CaptureFixture[str],
    operation: str,
) -> None:
    assert _DIAG.main([
        "--iterations", "1", "--mode", "separate-owner",
        "--startup-mode", "sequential", "--operation", operation,
        "--wal-keeper",
    ]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    result = json.loads(output.out)
    assert result["wal_keeper"] is True
    assert result["status_counts"] == {
        "UPDATED" if operation == "generation-cas" else "CREATED": 2,
    }
    assert result["anomalous_iterations"] == 0
    assert result["private_paths_exported"] is False
    assert result["safety_checks_relaxed"] is False
    assert result["sidecar_metadata_only"] == []
    for private in ("memory.sqlite", "ark-disposable-memory-", "owner-a", "source"):
        assert private not in output.out


def test_unmodified_default_has_no_wal_keeper() -> None:
    from inspect import signature

    assert signature(_DIAG._probe).parameters["wal_keeper"].default is False
