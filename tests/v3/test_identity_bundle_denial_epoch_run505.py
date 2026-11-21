"""Offline V3 identity evidence must not become approval via callbacks."""

import hashlib
from dataclasses import replace

import pytest

import ark.learning.identity_bundle_verify as mod
from ark.learning.execution import canonical_json


def pins(tmp_path):
    result = []
    for name, data in (
        ("base", {"revision": "local-fixture"}),
        ("tokenizer", {"chat_template_sha256": "a" * 64}),
    ):
        path = tmp_path / f"{name}.json"
        raw = canonical_json(data)
        path.write_bytes(raw)
        result.append(
            mod.LocalIdentityComponentPin(
                name, path, hashlib.sha256(raw).hexdigest(),
            ),
        )
    return tuple(result)


def verify(receipt, source):
    return mod.verify_local_identity_bundle(
        receipt, source, retained_bundle_sha256=receipt.bundle_sha256,
    )


@pytest.mark.parametrize("field,value", [
    ("components", ()),
    ("components", (("base", "f" * 64, 10, ()),)),
    ("bundle_sha256", "f" * 64),
    ("bundle_sha256", True),
])
def test_bundle_dataclass_equality_spoof_does_not_bypass_checks(
    tmp_path, monkeypatch, field, value,
):
    source = pins(tmp_path)
    original = mod.inspect_local_identity_bundle(source)
    forged = replace(original, **{field: value})
    monkeypatch.setattr(
        mod.LocalIdentityBundleWitness, "__eq__", lambda self, other: True,
    )
    with pytest.raises(mod.LocalIdentityBundleRejected):
        mod.verify_local_identity_bundle(
            forged, source, retained_bundle_sha256=original.bundle_sha256,
        )


def test_component_dataclass_equality_spoof_cannot_hide_changed_size(
    tmp_path, monkeypatch,
):
    source = pins(tmp_path)
    original = mod.verify_local_identity_artifact
    calls = 0

    def changed(path, *, retained_sha256):
        nonlocal calls
        result = original(path, retained_sha256=retained_sha256)
        calls += 1
        if calls == 3:
            return replace(result, artifact_bytes=result.artifact_bytes + 1)
        return result

    monkeypatch.setattr(mod, "verify_local_identity_artifact", changed)
    monkeypatch.setattr(
        mod.LocalIdentityArtifactWitness, "__eq__",
        lambda self, other: True,
    )
    with pytest.raises(mod.LocalIdentityBundleRejected, match="between reads"):
        mod.inspect_local_identity_bundle(source)


@pytest.mark.parametrize("mutation", ["receipt", "pin", "file"])
def test_final_denial_getter_cannot_hide_late_mutation(
    tmp_path, monkeypatch, mutation,
):
    source = pins(tmp_path)
    original = mod.inspect_local_identity_bundle(source)

    def denial(self):
        if self is original:
            if mutation == "receipt":
                object.__setattr__(self, "bundle_sha256", "f" * 64)
            elif mutation == "pin":
                object.__setattr__(source[0], "name", "different")
            else:
                source[0].path.write_bytes(canonical_json({"changed": True}))
        return False

    monkeypatch.setattr(
        mod.LocalIdentityBundleWitness,
        "protected_evaluation_authorized", property(denial),
    )
    with pytest.raises(mod.LocalIdentityBundleRejected):
        mod.verify_local_identity_bundle(
            original, source, retained_bundle_sha256=original.bundle_sha256,
        )


def test_bundle_constructor_late_result_mutation_detected(tmp_path, monkeypatch):
    source = pins(tmp_path)

    def denial(self):
        object.__setattr__(self, "components", ())
        return False

    monkeypatch.setattr(
        mod.LocalIdentityBundleWitness,
        "protected_evaluation_authorized", property(denial),
    )
    with pytest.raises(mod.LocalIdentityBundleRejected, match="changed"):
        mod.inspect_local_identity_bundle(source)


def test_valid_local_files_remain_unmodified_and_unauthorized(tmp_path):
    source = pins(tmp_path)
    before = tuple(pin.path.read_bytes() for pin in source)
    original = mod.inspect_local_identity_bundle(source)
    assert verify(original, source) is None
    assert tuple(pin.path.read_bytes() for pin in source) == before
    assert original.training_authorized is False
    assert original.candidate_generation_authorized is False
