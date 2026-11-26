"""Synthetic WAL diagnostic aggregation must not export forged probe labels.

Only two allowlisted child categories and an exact durable bool may reach
summary counters. No real user scope, external consent, retry or tool run.
"""

import json
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_revocation_wal_processes.py"
_SPEC = util.spec_from_file_location("revocation_wal_probe_admission_run900", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_DIAG = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DIAG)

_VALID = {"status": "REVOKED", "phase": "REVOKE"}


@pytest.mark.parametrize(
    "untrusted",
    [
        {"status": "REVOKED", "phase": "BOOTSTRAP"},
        {"status": "ALREADY", "phase": "UNKNOWN"},
        {"status": "secret/private/path", "phase": "REVOKE"},
        {"status": "SIDECAR_REFUSED", "phase": "UNKNOWN"},
        {"status": "OTHER_ERROR", "phase": "UNTRUSTED"},
        {"status": 1, "phase": "REVOKE"},
        {"status": "REVOKED", "phase": "REVOKE", "path": "secret"},
        ["REVOKED", "REVOKE"],
    ],
)
def test_malformed_probe_reply_is_bounded_and_never_passes(
    monkeypatch, capsys, untrusted,
):
    monkeypatch.setattr(
        _DIAG, "_probe", lambda _path, *, wal_keeper: (
            [untrusted, {"status": "ALREADY", "phase": "REVOKE"}], True
        ),
    )
    assert _DIAG.main(["--iterations", "1"]) == 1
    output = capsys.readouterr().out
    result = json.loads(output)
    assert result["durable_verified_iterations"] == 1
    assert result["durable_with_ambiguous_reply_iterations"] == 1
    assert result["status_counts"]["INVALID_REPLY"] == 1
    assert result["anomalous_iterations"] == 1
    assert "secret" not in output
    assert "UNTRUSTED" not in output
    assert result["automatic_retry"] is False


@pytest.mark.parametrize(
    ("probe_result", "durable"),
    [
        (([_VALID, {"status": "ALREADY", "phase": "REVOKE"}], 1), False),
        (([_VALID], True), False),
        (([_VALID, _VALID, _VALID], True), False),
        (({"unexpected": "shape"}, True), False),
        (("not-a-list", True), False),
        (([_VALID, _VALID], "yes"), False),
    ],
)
def test_probe_shape_or_untrusted_durability_is_not_certified(
    monkeypatch, capsys, probe_result, durable,
):
    monkeypatch.setattr(
        _DIAG, "_probe", lambda _path, *, wal_keeper: probe_result,
    )
    assert _DIAG.main(["--iterations", "1"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["durable_verified_iterations"] == int(durable)
    assert result["anomalous_iterations"] == 1


def test_valid_two_child_result_still_passes_without_granting_authority(
    monkeypatch, capsys,
):
    monkeypatch.setattr(
        _DIAG, "_probe",
        lambda _path, *, wal_keeper: (
            [_VALID, {"status": "ALREADY", "phase": "REVOKE"}], True
        ),
    )
    assert _DIAG.main(["--iterations", "1"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["anomalous_iterations"] == 0
    assert report["durable_verified_iterations"] == 1
    assert report["automatic_retry"] is False
    assert report["safety_checks_relaxed"] is False
    assert report["private_paths_exported"] is False
