"""V3 first-pass local artifact witnesses must remain stable through report return."""

import hashlib

import pytest

import ark.learning.identity_bundle_verify as mod
from ark.learning.execution import canonical_json


def _fixture(tmp_path):
    path = (tmp_path / "identity.json").resolve()
    data = canonical_json({"revision": "fixture-only"})
    path.write_bytes(data)
    pin = mod.LocalIdentityComponentPin(
        "model", path, hashlib.sha256(data).hexdigest(),
    )
    return (pin,), data


def _equal_but_new(original, field):
    if field == "top_level_keys":
        result = tuple(list(original))
    else:
        result = ("!" + original)[1:]
    assert result == original
    assert result is not original
    return result


@pytest.mark.parametrize("field", ("artifact_sha256", "top_level_keys"))
def test_second_verifier_cannot_replace_first_pass_carriers(
    tmp_path, monkeypatch, field,
):
    pins, data = _fixture(tmp_path)
    actual = mod.verify_local_identity_artifact
    first = None
    calls = 0

    def altered(path, *, retained_sha256):
        nonlocal first, calls
        witness = actual(path, retained_sha256=retained_sha256)
        calls += 1
        if calls == 1:
            first = witness
        else:
            old = getattr(first, field)
            object.__setattr__(first, field, _equal_but_new(old, field))
        return witness

    monkeypatch.setattr(mod, "verify_local_identity_artifact", altered)
    with pytest.raises(mod.LocalIdentityBundleRejected, match="first-pass"):
        mod.inspect_local_identity_bundle(pins)
    assert pins[0].path.read_bytes() == data


@pytest.mark.parametrize("field", ("artifact_sha256", "top_level_keys"))
def test_report_constructor_cannot_rewrite_first_pass_witness(
    tmp_path, monkeypatch, field,
):
    pins, data = _fixture(tmp_path)
    actual = mod.verify_local_identity_artifact
    first = None

    def observed(path, *, retained_sha256):
        nonlocal first
        witness = actual(path, retained_sha256=retained_sha256)
        if first is None:
            first = witness
        return witness

    constructor = mod.LocalIdentityBundleWitness.__init__

    def mutate_on_report(self, *args):
        constructor(self, *args)
        old = getattr(first, field)
        object.__setattr__(first, field, _equal_but_new(old, field))

    monkeypatch.setattr(mod, "verify_local_identity_artifact", observed)
    monkeypatch.setattr(mod.LocalIdentityBundleWitness, "__init__", mutate_on_report)
    with pytest.raises(mod.LocalIdentityBundleRejected, match="first-pass"):
        mod.inspect_local_identity_bundle(pins)
    assert pins[0].path.read_bytes() == data


def test_canonical_one_component_bundle_remains_inert_and_readonly(tmp_path):
    pins, data = _fixture(tmp_path)
    report = mod.inspect_local_identity_bundle(pins)
    assert report.source_authenticated is False
    assert report.training_authorized is False
    assert report.candidate_generation_authorized is False
    assert report.protected_evaluation_authorized is False
    assert len(report.bundle_sha256) == 64
    assert pins[0].path.read_bytes() == data
