"""No V3 packet verifier may return a witness after a late authority flip.

All records are synthetic review-only fixtures: no preflight, GPU, Candidate,
protected evaluation, paid service, or merge capability is exercised.
"""

from __future__ import annotations

import pytest
from test_authorization_packet_verify_run503 import _inputs

from ark.learning import authorization_packet_verify as verifier


@pytest.mark.parametrize("late_call", (1, 2, 3))
def test_final_false_getter_cannot_retroactively_grant_external_compute(
    monkeypatch: pytest.MonkeyPatch, late_call: int,
) -> None:
    snapshot, packet, retained = _inputs()
    invocations = 0
    with monkeypatch.context() as patch:

        def swap_earlier_authority(self: object) -> bool:
            nonlocal invocations
            invocations += 1
            if invocations == late_call:
                patch.setattr(
                    verifier.LocalPacketBindingWitness,
                    "external_compute_authorized",
                    property(lambda _self: True),
                )
            return False

        patch.setattr(
            verifier.LocalPacketBindingWitness,
            "main_merge_authorized",
            property(swap_earlier_authority),
        )
        with pytest.raises(verifier.LocalPacketBindingRejected, match="changed|authority"):
            verifier.verify_detached_authorization_packet(
                snapshot, packet, retained_packet_file_sha256=retained,
            )
    assert invocations >= late_call


def test_digest_getter_must_not_enable_permission_after_first_denial_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot, packet, retained = _inputs()
    descriptor = verifier.LocalPacketBindingWitness.snapshot_sha256
    calls = 0
    with monkeypatch.context() as patch:

        def late_digest_getter(self: object) -> str:
            nonlocal calls
            calls += 1
            value = descriptor.__get__(self, type(self))
            if calls == 2:
                patch.setattr(
                    verifier.LocalPacketBindingWitness,
                    "candidate_generation_authorized",
                    property(lambda _self: True),
                )
            return value

        def assign_digest(self: object, value: str) -> None:
            descriptor.__set__(self, value)

        patch.setattr(
            verifier.LocalPacketBindingWitness,
            "snapshot_sha256",
            property(late_digest_getter, assign_digest),
        )
        with pytest.raises(verifier.LocalPacketBindingRejected, match="changed|authority"):
            verifier.verify_detached_authorization_packet(
                snapshot, packet, retained_packet_file_sha256=retained,
            )
    assert calls >= 2
