"""Final offline V3 identity bundle scan detects late local file rewrites.

Only local fixture JSON is read. No model, GPU, Candidate or evaluation action.
"""

from __future__ import annotations

import hashlib
import os

import pytest

import ark.learning.identity_bundle_verify as bundle
from ark.learning.execution import canonical_json


def _fixture(tmp_path):
    first = (tmp_path / "first.json").resolve()
    second = (tmp_path / "second.json").resolve()
    first_bytes = canonical_json({"sample": "alpha"})
    second_bytes = canonical_json({"sample": "bravo"})
    first.write_bytes(first_bytes)
    second.write_bytes(second_bytes)
    pins = (
        bundle.LocalIdentityComponentPin(
            "a", first, hashlib.sha256(first_bytes).hexdigest(),
        ),
        bundle.LocalIdentityComponentPin(
            "b", second, hashlib.sha256(second_bytes).hexdigest(),
        ),
    )
    return pins, first, first_bytes


def _rewrite_same_size_with_restored_mtime(path, data):
    initial = path.stat()
    changed = data.replace(b"alpha", b"omega")
    assert len(changed) == len(data) and changed != data
    path.write_bytes(changed)
    os.utime(path, ns=(initial.st_atime_ns, initial.st_mtime_ns))


def test_bundle_rechecks_all_files_after_report_construction(tmp_path, monkeypatch):
    pins, path, data = _fixture(tmp_path)
    original = bundle.verify_local_identity_artifact
    observed = []

    def observe(target, *, retained_sha256):
        observed.append(target)
        return original(target, retained_sha256=retained_sha256)

    monkeypatch.setattr(bundle, "verify_local_identity_artifact", observe)
    report = bundle.inspect_local_identity_bundle(pins)
    assert observed == [
        pins[0].path, pins[1].path,
        pins[0].path, pins[1].path,
        pins[0].path, pins[1].path,
    ]
    assert report.bundle_sha256.startswith(("0", "1", "2", "3", "4", "5",
                                              "6", "7", "8", "9", "a", "b",
                                              "c", "d", "e", "f"))
    assert len(report.bundle_sha256) == 64
    assert report.source_authenticated is False
    assert report.training_authorized is False
    assert report.candidate_generation_authorized is False
    assert report.protected_evaluation_authorized is False
    assert path.read_bytes() == data


@pytest.mark.parametrize("replacement", ("constructor", "denial_getter"))
def test_late_same_size_timestamp_restored_rewrite_is_rejected(
    tmp_path, monkeypatch, replacement,
):
    pins, path, data = _fixture(tmp_path)
    if replacement == "constructor":
        original_init = bundle.LocalIdentityBundleWitness.__init__

        def alter_during_constructor(self, *args):
            original_init(self, *args)
            _rewrite_same_size_with_restored_mtime(path, data)

        monkeypatch.setattr(
            bundle.LocalIdentityBundleWitness, "__init__", alter_during_constructor,
        )
    else:
        injected = False

        def alter_during_authority_check(self):
            nonlocal injected
            if not injected:
                injected = True
                _rewrite_same_size_with_restored_mtime(path, data)
            return False

        monkeypatch.setattr(
            bundle.LocalIdentityBundleWitness,
            "source_authenticated",
            property(alter_during_authority_check),
        )

    diagnostic = (
        "after report" if replacement == "constructor"
        else "authority definition changed"
    )
    with pytest.raises(bundle.LocalIdentityBundleRejected, match=diagnostic):
        bundle.inspect_local_identity_bundle(pins)
    if replacement == "denial_getter":
        assert path.read_bytes() == data


def test_late_removal_is_not_reported_as_pinned_identity(tmp_path, monkeypatch):
    pins, path, _ = _fixture(tmp_path)
    original_init = bundle.LocalIdentityBundleWitness.__init__

    def remove_during_constructor(self, *args):
        original_init(self, *args)
        path.unlink()

    monkeypatch.setattr(
        bundle.LocalIdentityBundleWitness, "__init__", remove_during_constructor,
    )
    with pytest.raises(bundle.LocalIdentityBundleRejected, match="after report"):
        bundle.inspect_local_identity_bundle(pins)


def test_final_verifier_never_grants_training_or_candidate_permission(tmp_path):
    pins, _, _ = _fixture(tmp_path)
    report = bundle.inspect_local_identity_bundle(pins)
    bundle.verify_local_identity_bundle(
        report, pins, retained_bundle_sha256=report.bundle_sha256,
    )
    assert report.source_authenticated is False
    assert report.training_authorized is False
    assert report.candidate_generation_authorized is False
    assert report.protected_evaluation_authorized is False
