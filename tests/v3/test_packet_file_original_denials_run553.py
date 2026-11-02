"""Local V3 packet custody rejects replaced passive denial implementations.

Only synthetic local review packets are used. No compute, model or approval.
"""

from __future__ import annotations

import pytest

from ark.learning import authorization_packet_file_review as mod
from test_authorization_packet_file_review_run529 import _saved_packet


@pytest.mark.parametrize(
    "flag",
    (
        "external_compute_authorized",
        "candidate_generation_authorized",
        "protected_evaluation_authorized",
        "main_merge_authorized",
    ),
)
def test_preinstalled_false_only_denial_is_rejected_before_packet_io(
    tmp_path, monkeypatch, flag,
):
    snapshot, path, digest = _saved_packet(tmp_path)
    calls = []

    def replaced_false(_self):
        calls.append("property invoked")
        return False

    def forbidden_read(_path):
        calls.append("file read")
        raise AssertionError("must reject before reading the packet")

    monkeypatch.setattr(
        mod.LocalPacketBindingWitness, flag, property(replaced_false),
    )
    monkeypatch.setattr(mod, "_read_exact_local_packet", forbidden_read)
    with pytest.raises(mod.LocalPacketBindingRejected, match="descriptor changed"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )
    assert calls == []


def test_delegated_verifier_cannot_install_new_false_denial(
    tmp_path, monkeypatch,
):
    snapshot, path, digest = _saved_packet(tmp_path)
    original = mod.verify_detached_authorization_packet
    seen = []

    def swap_on_return(*args, **kwargs):
        witness = original(*args, **kwargs)
        seen.append("verified")
        monkeypatch.setattr(
            mod.LocalPacketBindingWitness,
            "main_merge_authorized",
            property(lambda _self: False),
        )
        return witness

    monkeypatch.setattr(mod, "verify_detached_authorization_packet", swap_on_return)
    with pytest.raises(mod.LocalPacketBindingRejected, match="descriptor changed"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )
    assert seen == ["verified"]


def test_packet_read_callback_cannot_replace_denial_before_verification(
    tmp_path, monkeypatch,
):
    snapshot, path, digest = _saved_packet(tmp_path)
    original_read = mod._read_exact_local_packet
    called = []

    def read_then_swap(target):
        data = original_read(target)
        monkeypatch.setattr(
            mod.LocalPacketBindingWitness,
            "protected_evaluation_authorized",
            property(lambda _self: False),
        )
        return data

    def forbidden_verify(*args, **kwargs):
        called.append("verifier invoked")
        raise AssertionError("verification must not run after descriptor change")

    monkeypatch.setattr(mod, "_read_exact_local_packet", read_then_swap)
    monkeypatch.setattr(
        mod, "verify_detached_authorization_packet", forbidden_verify,
    )
    with pytest.raises(mod.LocalPacketBindingRejected, match="descriptor changed"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )
    assert called == []


def test_rebinding_witness_class_name_does_not_supply_new_baseline(
    tmp_path, monkeypatch,
):
    snapshot, path, digest = _saved_packet(tmp_path)
    monkeypatch.setattr(mod, "LocalPacketBindingWitness", object)
    with pytest.raises(mod.LocalPacketBindingRejected, match="descriptor changed"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )


def test_untouched_packet_still_returns_non_authorizing_witness(tmp_path):
    snapshot, path, digest = _saved_packet(tmp_path)
    witness = mod.verify_local_authorization_packet_file(
        snapshot, path, retained_packet_file_sha256=digest,
    )
    assert type(witness) is mod.LocalPacketBindingWitness
    assert witness.packet_file_sha256 == digest
    assert witness.external_compute_authorized is False
    assert witness.candidate_generation_authorized is False
    assert witness.protected_evaluation_authorized is False
    assert witness.main_merge_authorized is False
