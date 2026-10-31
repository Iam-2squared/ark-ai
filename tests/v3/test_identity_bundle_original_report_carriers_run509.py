"""V3 local identity bundle must retain original report carriers across callbacks.

Offline JSON identity inspection is never approval for paid GPU, Candidate
generation, protected evaluation or external training.
"""

import hashlib

import pytest

import ark.learning.identity_bundle_verify as mod
from ark.learning.execution import canonical_json


def _state(tmp_path):
    path = (tmp_path / "base.json").resolve()
    raw = canonical_json({"revision": "fixture-local"})
    path.write_bytes(raw)
    pins = (mod.LocalIdentityComponentPin(
        "base", path, hashlib.sha256(raw).hexdigest(),
    ),)
    return pins, mod.inspect_local_identity_bundle(pins), raw


def _verify(pins, report):
    return mod.verify_local_identity_bundle(
        report, pins, retained_bundle_sha256=report.bundle_sha256,
    )


def _equal_new(original, kind):
    if kind == "tuple":
        copied = tuple(list(original))
    else:
        copied = ("!" + original)[1:]
    assert copied == original
    assert copied is not original
    return copied


@pytest.mark.parametrize("kind", ("tuple", "digest"))
def test_local_component_callback_cannot_retarget_equal_report(
    tmp_path, monkeypatch, kind,
):
    pins, report, original_bytes = _state(tmp_path)
    actual = mod.verify_local_identity_artifact
    calls = 0

    def changed(path, *, retained_sha256):
        nonlocal calls
        witness = actual(path, retained_sha256=retained_sha256)
        calls += 1
        if calls == 1:
            field = "components" if kind == "tuple" else "bundle_sha256"
            object.__setattr__(
                report, field, _equal_new(getattr(report, field), kind),
            )
        return witness

    monkeypatch.setattr(mod, "verify_local_identity_artifact", changed)
    with pytest.raises(mod.LocalIdentityBundleRejected, match="root mismatch"):
        _verify(pins, report)
    assert pins[0].path.read_bytes() == original_bytes


@pytest.mark.parametrize("kind", ("tuple", "digest"))
def test_false_denial_getter_cannot_retarget_equal_bundle_carrier(
    tmp_path, monkeypatch, kind,
):
    pins, report, original_bytes = _state(tmp_path)

    def denial(self):
        if self is report:
            field = "components" if kind == "tuple" else "bundle_sha256"
            object.__setattr__(
                self, field, _equal_new(getattr(self, field), kind),
            )
        return False

    monkeypatch.setattr(
        mod.LocalIdentityBundleWitness,
        "protected_evaluation_authorized", property(denial),
    )
    with pytest.raises(mod.LocalIdentityBundleRejected, match="changed after denial"):
        _verify(pins, report)
    assert pins[0].path.read_bytes() == original_bytes


def test_canonical_local_files_remain_readonly_and_non_authorizing(tmp_path):
    pins, report, original_bytes = _state(tmp_path)
    assert _verify(pins, report) is None
    assert pins[0].path.read_bytes() == original_bytes
    assert report.source_authenticated is False
    assert report.training_authorized is False
    assert report.candidate_generation_authorized is False
    assert report.protected_evaluation_authorized is False
