"""Passive V3 packet binding cannot inherit substituted false-only authority."""

import pytest
from test_authorization_packet_verify_run503 import _inputs

from ark.learning import authorization_packet_verify as verifier


@pytest.mark.parametrize("name", verifier._DENIAL_FLAGS)
def test_preinstalled_false_only_denial_is_not_original(monkeypatch, name):
    snapshot, packet, retained = _inputs()
    monkeypatch.setattr(
        verifier.LocalPacketBindingWitness,
        name,
        property(lambda _self: False),
    )
    with pytest.raises(verifier.LocalPacketBindingRejected, match="descriptor"):
        verifier.verify_detached_authorization_packet(
            snapshot, packet, retained_packet_file_sha256=retained,
        )


def test_late_false_only_authority_replacement_is_rejected(monkeypatch):
    snapshot, packet, retained = _inputs()
    original = verifier.LocalPacketBindingWitness.snapshot_sha256
    calls = 0

    def swap_after_witness_construction(self):
        nonlocal calls
        calls += 1
        value = original.__get__(self, type(self))
        if calls == 2:
            monkeypatch.setattr(
                verifier.LocalPacketBindingWitness,
                "external_compute_authorized",
                property(lambda _self: False),
            )
        return value

    def set_digest(self, value):
        original.__set__(self, value)

    monkeypatch.setattr(
        verifier.LocalPacketBindingWitness,
        "snapshot_sha256",
        property(swap_after_witness_construction, set_digest),
    )
    with pytest.raises(verifier.LocalPacketBindingRejected, match="descriptor"):
        verifier.verify_detached_authorization_packet(
            snapshot, packet, retained_packet_file_sha256=retained,
        )
    assert calls >= 2


def test_unmodified_v3_packet_stays_passive():
    snapshot, packet, retained = _inputs()
    result = verifier.verify_detached_authorization_packet(
        snapshot, packet, retained_packet_file_sha256=retained,
    )
    for name in verifier._DENIAL_FLAGS:
        assert getattr(result, name) is False
    assert result.packet_file_sha256 == retained
