"""Privacy-safe phase aggregates for a disposable WAL diagnostic.

No subprocesses, real Memory, user data, or revocation operations are
performed by these aggregate-only synthetic fault cases.
"""

import json
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_revocation_wal_processes.py"
_SPEC = util.spec_from_file_location("revocation_wal_phase_run893", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_DIAG = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DIAG)


def _reply(status: str, phase: str) -> dict[str, str]:
    return {"status": status, "phase": phase}


@pytest.mark.parametrize(
    ("replies", "durable", "exit_code", "verified", "ambiguous"),
    (
        ([_reply("REVOKED", "REVOKE"), _reply("ALREADY", "REVOKE")],
         True, 0, 1, 0),
        ([_reply("REVOKED", "REVOKE"), _reply("SIDECAR_REFUSED", "REVOKE")],
         True, 1, 1, 1),
        ([_reply("REVOKED", "REVOKE"), _reply("ALREADY", "REVOKE")],
         False, 1, 0, 0),
        ([_reply("SIDECAR_REFUSED", "BOOTSTRAP"),
          _reply("ALREADY", "REVOKE")], True, 1, 1, 1),
    ),
)
def test_status_phase_aggregate_separates_durable_veto_from_child_reply(
    monkeypatch, capsys, replies, durable, exit_code, verified, ambiguous,
):
    def fake_probe(_path, *, wal_keeper=False):
        assert wal_keeper is False
        return replies, durable

    monkeypatch.setattr(_DIAG, "_probe", fake_probe)
    assert _DIAG.main(["--iterations", "1"]) == exit_code
    result = json.loads(capsys.readouterr().out)
    assert result["durable_verified_iterations"] == verified
    assert result["durable_with_ambiguous_reply_iterations"] == ambiguous
    assert result["anomalous_iterations"] == exit_code
    assert result["status_phase_counts"] == {
        f'{row["phase"]}:{row["status"]}': 1 for row in replies
    }
    assert result["private_paths_exported"] is False
    assert result["safety_checks_relaxed"] is False
    assert result["automatic_retry"] is False
    assert "revocation.sqlite" not in json.dumps(result)


def test_second_iteration_adds_counts_without_private_path_echo(monkeypatch, capsys):
    calls = []

    def fake_probe(path, *, wal_keeper=False):
        calls.append(path)
        assert wal_keeper
        return ([_reply("REVOKED", "REVOKE"), _reply("ALREADY", "REVOKE")],
                True)

    monkeypatch.setattr(_DIAG, "_probe", fake_probe)
    assert _DIAG.main(["--iterations", "2", "--wal-keeper"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert len(calls) == 2
    assert report["status_phase_counts"] == {
        "REVOKE:ALREADY": 2, "REVOKE:REVOKED": 2,
    }
    assert report["durable_verified_iterations"] == 2
    assert report["durable_with_ambiguous_reply_iterations"] == 0
    assert all(str(path) not in json.dumps(report) for path in calls)
