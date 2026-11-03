"""Read-only local V3 JSON bundle review; no Candidate, GPU or training."""

import hashlib
from dataclasses import replace

import pytest

import ark.learning.identity_bundle_verify as mod
from ark.learning.execution import canonical_json


def fixture(tmp_path):
    base = tmp_path / "base.json"
    tok = tmp_path / "tokenizer.json"
    base_raw = canonical_json({"revision": "offline-example"})
    tok_raw = canonical_json({"chat_template_sha256": "a" * 64})
    base.write_bytes(base_raw)
    tok.write_bytes(tok_raw)
    pins = (
        mod.LocalIdentityComponentPin(
            "base", base, hashlib.sha256(base_raw).hexdigest(),
        ),
        mod.LocalIdentityComponentPin(
            "tokenizer", tok, hashlib.sha256(tok_raw).hexdigest(),
        ),
    )
    return pins


def test_deterministic_bundle_and_independent_root(tmp_path):
    pins = fixture(tmp_path)
    report = mod.inspect_local_identity_bundle(pins)
    assert report == mod.inspect_local_identity_bundle(pins)
    assert len(report.components) == 2
    assert len(report.bundle_sha256) == 64
    assert tuple(row[0] for row in report.components) == ("base", "tokenizer")
    assert mod.verify_local_identity_bundle(
        report, pins, retained_bundle_sha256=report.bundle_sha256,
    ) is None
    for flag in mod._FLAGS:
        assert getattr(report, flag) is False


def test_bundle_reads_do_not_modify_files(tmp_path):
    pins = fixture(tmp_path)
    before = tuple(pin.path.read_bytes() for pin in pins)
    mod.inspect_local_identity_bundle(pins)
    assert tuple(pin.path.read_bytes() for pin in pins) == before


@pytest.mark.parametrize("bad_kind", [
    "reversed", "list", "duplicate_label", "duplicate_path", "bad_label",
    "bool_hash", "bad_sha", "relative_path", "unknown_type", "missing",
])
def test_invalid_bounded_bundle_pins_rejected(tmp_path, bad_kind):
    pins = fixture(tmp_path)
    if bad_kind == "reversed":
        bad = pins[::-1]
    elif bad_kind == "list":
        bad = list(pins)
    elif bad_kind == "duplicate_label":
        bad = (pins[0], replace(pins[1], name="base"))
    elif bad_kind == "duplicate_path":
        bad = (pins[0], replace(pins[1], path=pins[0].path))
    elif bad_kind == "bad_label":
        bad = (replace(pins[0], name="../base"), pins[1])
    elif bad_kind == "bool_hash":
        bad = (replace(pins[0], retained_sha256=True), pins[1])
    elif bad_kind == "bad_sha":
        bad = (replace(pins[0], retained_sha256="f" * 64), pins[1])
    elif bad_kind == "relative_path":
        bad = (replace(pins[0], path=pins[0].path.relative_to(tmp_path)), pins[1])
    elif bad_kind == "unknown_type":
        bad = (True, pins[1])
    else:
        bad = (replace(pins[0], path=tmp_path / "missing.json"), pins[1])
    with pytest.raises(mod.LocalIdentityBundleRejected):
        mod.inspect_local_identity_bundle(bad)


@pytest.mark.parametrize("size", [0, 9])
def test_component_count_budget_rejected(tmp_path, size):
    pins = fixture(tmp_path)
    with pytest.raises(mod.LocalIdentityBundleRejected):
        mod.inspect_local_identity_bundle(pins[:0] if size == 0 else pins * 5)


@pytest.mark.parametrize("field,bad", [
    ("bundle_sha256", "f" * 64),
    ("bundle_sha256", True),
    ("components", ()),
    ("components", (("base", "0" * 64, 1, ()),)),
    ("components", [[True]]),
])
def test_forged_report_rejected(tmp_path, field, bad):
    pins = fixture(tmp_path)
    original = mod.inspect_local_identity_bundle(pins)
    fake = replace(original, **{field: bad})
    with pytest.raises(mod.LocalIdentityBundleRejected):
        mod.verify_local_identity_bundle(
            fake, pins, retained_bundle_sha256=original.bundle_sha256,
        )


@pytest.mark.parametrize("root", [True, "f" * 64, "x", "A" * 64])
def test_wrong_retained_root_rejected(tmp_path, root):
    pins = fixture(tmp_path)
    report = mod.inspect_local_identity_bundle(pins)
    with pytest.raises(mod.LocalIdentityBundleRejected):
        mod.verify_local_identity_bundle(
            report, pins, retained_bundle_sha256=root,
        )


def test_component_mutated_between_first_and_second_pass(tmp_path, monkeypatch):
    pins = fixture(tmp_path)
    original = mod.verify_local_identity_artifact
    called = 0

    def race(path, *, retained_sha256):
        nonlocal called
        witness = original(path, retained_sha256=retained_sha256)
        called += 1
        if called == 2:
            pins[0].path.write_bytes(canonical_json({"changed": True}))
        return witness

    monkeypatch.setattr(mod, "verify_local_identity_artifact", race)
    with pytest.raises(mod.LocalIdentityBundleRejected, match="between reads"):
        mod.inspect_local_identity_bundle(pins)


def test_changed_pin_carrier_during_file_callback_denied(tmp_path, monkeypatch):
    pins = fixture(tmp_path)
    original = mod.verify_local_identity_artifact

    def race(path, *, retained_sha256):
        object.__setattr__(pins[0], "name", "different")
        return original(path, retained_sha256=retained_sha256)

    monkeypatch.setattr(mod, "verify_local_identity_artifact", race)
    with pytest.raises(mod.LocalIdentityBundleRejected, match="carriers changed"):
        mod.inspect_local_identity_bundle(pins)


@pytest.mark.parametrize("flag", mod._FLAGS)
def test_bundle_witness_does_not_gain_authority(tmp_path, monkeypatch, flag):
    pins = fixture(tmp_path)
    monkeypatch.setattr(
        mod.LocalIdentityBundleWitness, flag,
        property(lambda self: True),
    )
    with pytest.raises(mod.LocalIdentityBundleRejected, match="authority"):
        mod.inspect_local_identity_bundle(pins)


def test_component_witness_cannot_claim_training_permission(tmp_path, monkeypatch):
    pins = fixture(tmp_path)
    original = mod.verify_local_identity_artifact

    def fake(path, *, retained_sha256):
        witness = original(path, retained_sha256=retained_sha256)
        object.__setattr__(witness, "artifact_sha256", "f" * 64)
        return witness

    monkeypatch.setattr(mod, "verify_local_identity_artifact", fake)
    with pytest.raises(mod.LocalIdentityBundleRejected, match="authority"):
        mod.inspect_local_identity_bundle(pins)


class ForgedBundleWitness(mod.LocalIdentityBundleWitness):
    pass


def test_subclass_report_not_accepted(tmp_path):
    pins = fixture(tmp_path)
    receipt = mod.inspect_local_identity_bundle(pins)
    fake = ForgedBundleWitness(receipt.components, receipt.bundle_sha256)
    with pytest.raises(mod.LocalIdentityBundleRejected, match="exact"):
        mod.verify_local_identity_bundle(
            fake, pins, retained_bundle_sha256=receipt.bundle_sha256,
        )
