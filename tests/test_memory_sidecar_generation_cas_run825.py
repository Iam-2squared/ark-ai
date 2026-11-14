"""Actual generation-fenced SQLite CAS under disposable independent processes.

The diagnostic must not substitute a create for a CAS update, suppress
independent-owner conflicts, or emit private filesystem/row/token bytes.
No real memory, external executor, action authorization or paid compute.
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


def _diagnostic():
    spec = util.spec_from_file_location("ark_sidecar_generation_cas_run825", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _diagnostic()


@pytest.mark.parametrize(
    ("mode", "expected"),
    (
        ("same-identity", ("CONFLICT", "UPDATED")),
        ("separate-owner", ("UPDATED", "UPDATED")),
        ("separate-namespace", ("UPDATED", "UPDATED")),
        ("separate-source", ("UPDATED", "UPDATED")),
    ),
)
def test_real_fenced_cas_cross_process_preserves_rows_and_events(
    tmp_path: Path, mode: str, expected: tuple[str, str],
) -> None:
    path = tmp_path / "memory.sqlite"
    outcomes = _DIAG._probe(path, mode, "sequential", "generation-cas")
    assert len(outcomes) == 2
    assert tuple(sorted(item["status"] for item in outcomes)) == expected
    report = json.dumps(outcomes, sort_keys=True)
    assert str(tmp_path) not in report
    assert "memory.sqlite" not in report
    assert "owner-a" not in report
    assert "owner-b" not in report
    assert "fixture" not in report

    identities = [("owner-a", "fixture", "source")]
    if mode == "separate-owner":
        identities.append(("owner-b", "fixture", "source"))
    elif mode == "separate-namespace":
        identities.append(("owner-a", "other", "source"))
    elif mode == "separate-source":
        identities.append(("owner-a", "fixture", "other"))
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 1001)
    for owner, namespace, source in identities:
        scope = MemoryScope(owner, namespace)
        memory_id = deterministic_memory_id(scope, source)
        record = cold.get(memory_id, scope)
        assert record is not None
        assert record.revision == 2
        assert record.content == "fixture"
        events = [event for event in cold.events(scope) if event.memory_id == memory_id]
        assert [event.operation for event in events] == ["create", "update"]
    assert sum(len(cold.events(MemoryScope(owner, namespace)))
               for owner, namespace in {
                   (owner, namespace) for owner, namespace, _ in identities
               }) == 2 * len(identities)


@pytest.mark.parametrize("mode", ("same-identity", "separate-owner"))
def test_generation_cas_cli_returns_only_aggregate_receipt(
    capsys: pytest.CaptureFixture[str], mode: str,
) -> None:
    assert _DIAG.main([
        "--iterations", "1", "--mode", mode,
        "--startup-mode", "sequential", "--operation", "generation-cas",
    ]) == 0
    capture = capsys.readouterr()
    receipt = json.loads(capture.out)
    assert capture.err == ""
    assert receipt["operation"] == "generation-cas"
    assert receipt["anomalous_iterations"] == 0
    expected = (
        {"CONFLICT": 1, "UPDATED": 1}
        if mode == "same-identity" else {"UPDATED": 2}
    )
    assert receipt["status_counts"] == expected
    assert receipt["private_paths_exported"] is False
    assert receipt["safety_checks_relaxed"] is False
    assert receipt["sidecar_metadata_only"] == []
    for secret in ("owner-a", "owner-b", "memory.sqlite", "source", "before"):
        assert secret not in capture.out


def test_unknown_operation_rejected_without_starting_children(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown disposable diagnostic operation"):
        _DIAG._probe(tmp_path / "memory.sqlite", "same-identity", "sequential", "dispatch")
    assert not (tmp_path / "release").exists()
