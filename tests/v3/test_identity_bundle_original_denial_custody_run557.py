"""Identity bundle source and component reports require original denials.

Only local synthetic JSON is read. No HF byte provenance, user approval,
billable compute, Candidate output or protected evaluation is established.
"""

from __future__ import annotations

import pytest
from test_identity_bundle_verify_run502 import fixture

import ark.learning.identity_bundle_verify as mod


@pytest.mark.parametrize("carrier", ("bundle", "component"))
@pytest.mark.parametrize("flag", mod._FLAGS)
def test_false_only_preinstalled_getter_rejected_before_bundle_inspection(
    tmp_path, monkeypatch, carrier, flag,
):
    pins = fixture(tmp_path)
    source_bytes = tuple(pin.path.read_bytes() for pin in pins)
    cls = (
        mod.LocalIdentityBundleWitness if carrier == "bundle"
        else mod.LocalIdentityArtifactWitness
    )
    monkeypatch.setattr(cls, flag, property(lambda _self: False))
    with pytest.raises(
        mod.LocalIdentityBundleRejected, match="authority definition changed",
    ):
        mod.inspect_local_identity_bundle(pins)
    assert tuple(pin.path.read_bytes() for pin in pins) == source_bytes


@pytest.mark.parametrize("carrier", ("bundle", "component"))
@pytest.mark.parametrize("flag", mod._FLAGS)
def test_false_only_preinstalled_getter_rejected_before_retained_recheck(
    tmp_path, monkeypatch, carrier, flag,
):
    pins = fixture(tmp_path)
    report = mod.inspect_local_identity_bundle(pins)
    cls = (
        mod.LocalIdentityBundleWitness if carrier == "bundle"
        else mod.LocalIdentityArtifactWitness
    )
    monkeypatch.setattr(cls, flag, property(lambda _self: False))
    with pytest.raises(
        mod.LocalIdentityBundleRejected, match="authority definition changed",
    ):
        mod.verify_local_identity_bundle(
            report, pins, retained_bundle_sha256=report.bundle_sha256,
        )


@pytest.mark.parametrize("carrier", ("bundle", "component"))
def test_file_callback_cannot_rebaseline_false_only_denial(
    tmp_path, monkeypatch, carrier,
):
    pins = fixture(tmp_path)
    native = mod.verify_local_identity_artifact
    cls = (
        mod.LocalIdentityBundleWitness if carrier == "bundle"
        else mod.LocalIdentityArtifactWitness
    )
    calls = []

    def replace_during_first_verification(*args, **kwargs):
        result = native(*args, **kwargs)
        calls.append(1)
        if len(calls) == 1:
            monkeypatch.setattr(
                cls, "training_authorized", property(lambda _self: False),
            )
        return result

    monkeypatch.setattr(
        mod, "verify_local_identity_artifact", replace_during_first_verification,
    )
    with pytest.raises(
        mod.LocalIdentityBundleRejected, match="authority definition changed",
    ):
        mod.inspect_local_identity_bundle(pins)
    assert calls


def test_intact_identity_bundle_remains_unapproved_and_readonly(tmp_path):
    pins = fixture(tmp_path)
    source_bytes = tuple(pin.path.read_bytes() for pin in pins)
    report = mod.inspect_local_identity_bundle(pins)
    mod.verify_local_identity_bundle(
        report, pins, retained_bundle_sha256=report.bundle_sha256,
    )
    assert tuple(pin.path.read_bytes() for pin in pins) == source_bytes
    for flag in mod._FLAGS:
        assert getattr(report, flag) is False
