"""Final V3 local bundle verification cannot inherit late authority flags.

Fixture JSON and local hashes only: no training, GPU, model download, real
Candidate, protected V2 final evaluation or approval is performed.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.learning.identity_bundle_verify as bundle
from ark.learning.execution import canonical_json


def _state(tmp_path):
    path = (tmp_path / "local_identity.json").resolve()
    data = canonical_json({"fixture": "not a model"})
    path.write_bytes(data)
    pins = (bundle.LocalIdentityComponentPin(
        "local", path, hashlib.sha256(data).hexdigest(),
    ),)
    report = bundle.inspect_local_identity_bundle(pins)
    return pins, report, data


def _review(report, pins):
    return bundle.verify_local_identity_bundle(
        report, pins, retained_bundle_sha256=report.bundle_sha256,
    )


@pytest.mark.parametrize("flag", (
    "source_authenticated", "training_authorized",
    "candidate_generation_authorized", "protected_evaluation_authorized",
))
def test_retained_report_cannot_gain_flag_during_final_disk_read(
    tmp_path, monkeypatch, flag,
):
    pins, report, data = _state(tmp_path)
    inspect = bundle.inspect_local_identity_bundle
    checks = 0
    armed = False

    def late_inspect(value):
        nonlocal checks, armed
        latest = inspect(value)
        checks += 1
        if checks == 2:
            armed = True
            monkeypatch.setattr(
                bundle.LocalIdentityBundleWitness, flag,
                property(lambda self: bool(armed and self is report)),
            )
        return latest

    monkeypatch.setattr(bundle, "inspect_local_identity_bundle", late_inspect)
    with pytest.raises(bundle.LocalIdentityBundleRejected, match="changed"):
        _review(report, pins)
    assert checks == 2
    assert pins[0].path.read_bytes() == data


@pytest.mark.parametrize("flag", (
    "source_authenticated", "candidate_generation_authorized",
))
def test_newly_rechecked_local_report_must_also_have_no_authority(
    tmp_path, monkeypatch, flag,
):
    pins, report, data = _state(tmp_path)
    inspect = bundle.inspect_local_identity_bundle
    latest_report = None
    calls = 0

    def late_inspect(value):
        nonlocal calls, latest_report
        result = inspect(value)
        calls += 1
        if calls == 2:
            latest_report = result
            monkeypatch.setattr(
                bundle.LocalIdentityBundleWitness, flag,
                property(lambda self: bool(self is latest_report)),
            )
        return result

    monkeypatch.setattr(bundle, "inspect_local_identity_bundle", late_inspect)
    with pytest.raises(bundle.LocalIdentityBundleRejected, match="changed"):
        _review(report, pins)
    assert calls == 2
    assert pins[0].path.read_bytes() == data


def test_late_denial_getter_may_not_replace_retained_report_carrier(
    tmp_path, monkeypatch,
):
    pins, report, data = _state(tmp_path)
    original_digest = report.bundle_sha256
    accesses = 0

    def late_false(self):
        nonlocal accesses
        if self is report:
            accesses += 1
            if accesses == 2:
                replacement = ("!" + self.bundle_sha256)[1:]
                assert replacement == self.bundle_sha256
                assert replacement is not self.bundle_sha256
                object.__setattr__(self, "bundle_sha256", replacement)
        return False

    monkeypatch.setattr(
        bundle.LocalIdentityBundleWitness,
        "source_authenticated",
        property(late_false),
    )
    with pytest.raises(bundle.LocalIdentityBundleRejected):
        _review(report, pins)
    # A substituted getter is rejected before the first reflective read.
    assert accesses == 0
    assert report.bundle_sha256 is original_digest
    assert pins[0].path.read_bytes() == data


def test_valid_offline_bundle_still_has_no_external_authority(tmp_path):
    pins, report, data = _state(tmp_path)
    assert _review(report, pins) is None
    assert pins[0].path.read_bytes() == data
    for flag in bundle._FLAGS:
        assert getattr(report, flag) is False
