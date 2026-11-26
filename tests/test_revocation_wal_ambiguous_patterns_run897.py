"""Bounded synthetic winner/loser classifications for WAL revocation probes.

No private scope, user database, backend, approval or retry is involved.
A durable row is evidence of a synthetic committed veto, never authority.
"""

import json
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_revocation_wal_processes.py"
_SPEC = util.spec_from_file_location("revocation_wal_patterns_run897", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_DIAG = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DIAG)


def _pair(a_status, a_phase, b_status, b_phase):
    return [
        {"status": a_status, "phase": a_phase},
        {"status": b_status, "phase": b_phase},
    ]


@pytest.mark.parametrize(
    ("phase", "expected_pattern"),
    [
        ("BOOTSTRAP", "BOOTSTRAP:SIDECAR_REFUSED + REVOKE:REVOKED"),
        ("REVOKE", "REVOKE:REVOKED + REVOKE:SIDECAR_REFUSED"),
    ],
)
def test_committed_winner_and_refused_loser_are_reported_separately(
    monkeypatch, capsys, phase, expected_pattern,
):
    monkeypatch.setattr(
        _DIAG,
        "_probe",
        lambda _path, *, wal_keeper: (
            _pair("REVOKED", "REVOKE", "SIDECAR_REFUSED", phase), True
        ),
    )
    assert _DIAG.main(["--iterations", "2"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["durable_verified_iterations"] == 2
    assert report["durable_with_ambiguous_reply_iterations"] == 2
    assert report["durable_ambiguous_phase_patterns"] == {expected_pattern: 2}
    assert report["unverified_phase_patterns"] == {}
    assert report["anomalous_iterations"] == 2
    assert report["automatic_retry"] is False
    assert report["safety_checks_relaxed"] is False
    assert report["private_paths_exported"] is False


def test_successful_child_replies_without_durable_readback_are_not_pass(
    monkeypatch, capsys,
):
    monkeypatch.setattr(
        _DIAG,
        "_probe",
        lambda _path, *, wal_keeper: (
            _pair("REVOKED", "REVOKE", "ALREADY", "REVOKE"), False
        ),
    )
    assert _DIAG.main(["--iterations", "1"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["durable_verified_iterations"] == 0
    assert report["durable_with_ambiguous_reply_iterations"] == 0
    assert report["durable_ambiguous_phase_patterns"] == {}
    assert report["unverified_phase_patterns"] == {
        "REVOKE:ALREADY + REVOKE:REVOKED": 1,
    }
    assert report["anomalous_iterations"] == 1


def test_exact_two_child_success_with_durable_readback_has_no_anomaly(
    monkeypatch, capsys,
):
    monkeypatch.setattr(
        _DIAG,
        "_probe",
        lambda _path, *, wal_keeper: (
            _pair("ALREADY", "REVOKE", "REVOKED", "REVOKE"), True
        ),
    )
    assert _DIAG.main(["--iterations", "1", "--wal-keeper"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["wal_keeper"] is True
    assert report["durable_verified_iterations"] == 1
    assert report["durable_with_ambiguous_reply_iterations"] == 0
    assert report["durable_ambiguous_phase_patterns"] == {}
    assert report["unverified_phase_patterns"] == {}
    assert report["anomalous_iterations"] == 0


def test_reply_parser_does_not_accept_fake_pre_gate_success():
    for status in ("REVOKED", "ALREADY"):
        assert _DIAG._parse_reply(
            json.dumps({"status": status, "phase": "BOOTSTRAP"})
        ) == {"status": "INVALID_REPLY", "phase": "UNKNOWN"}
