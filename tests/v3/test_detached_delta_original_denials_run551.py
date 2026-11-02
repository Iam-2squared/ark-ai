"""Detached unapproved V3 receipts reject preinstalled False-only authority swaps."""

from __future__ import annotations

import hashlib

import pytest

from ark.learning import authorization_packet_delta_recheck as mod
from ark.learning import authorization_packet_delta_review as base
from ark.learning.execution import canonical_json


def _receipt():
    old, new, paths = "a" * 64, "b" * 64, ("unapproved.path",)
    digest = hashlib.sha256(
        b"ARK-v3-unapproved-packet-delta-review-v1\\0"
        + canonical_json((old, new, paths))
    ).hexdigest()
    return base.ReviewPacketDelta(old, new, paths, digest)


def _check(monkeypatch, receipt):
    # Unit-only fake re-review. Existing integration tests separately verify
    # that real packet files are re-read. No path here is an approval source.
    monkeypatch.setattr(
        mod, "review_unapproved_packet_delta",
        lambda *args, **kwargs: receipt,
    )
    return mod.verify_detached_unapproved_packet_delta(
        receipt, {}, {}, object(), object(),
        retained_old_file_sha256="a" * 64,
        retained_new_file_sha256="b" * 64,
    )


@pytest.mark.parametrize("flag", (
    "external_compute_authorized", "candidate_generation_authorized",
    "protected_evaluation_authorized", "main_merge_authorized",
))
def test_preinstalled_false_only_property_cannot_become_original(
    monkeypatch, flag,
):
    receipt = _receipt()
    monkeypatch.setattr(
        base.ReviewPacketDelta, flag, property(lambda self: False),
    )

    def should_not_run(*args, **kwargs):
        raise AssertionError("detached source re-review must not run")

    monkeypatch.setattr(mod, "review_unapproved_packet_delta", should_not_run)
    with pytest.raises(mod.DetachedPacketDeltaRejected, match="descriptor changed"):
        mod.verify_detached_unapproved_packet_delta(
            receipt, {}, {}, object(), object(),
            retained_old_file_sha256="a" * 64,
            retained_new_file_sha256="b" * 64,
        )


def test_preinstalled_false_getter_with_callback_is_rejected(monkeypatch):
    receipt = _receipt()
    calls = []

    def callback(self):
        calls.append(self)
        return False

    monkeypatch.setattr(
        base.ReviewPacketDelta, "main_merge_authorized", property(callback),
    )
    with pytest.raises(mod.DetachedPacketDeltaRejected, match="descriptor changed"):
        _check(monkeypatch, receipt)
    assert not calls


def test_original_denials_preserve_inert_mock_review(monkeypatch):
    receipt = _receipt()
    assert _check(monkeypatch, receipt) is None
    assert receipt.external_compute_authorized is False
    assert receipt.protected_evaluation_authorized is False


@pytest.mark.parametrize("field", ("delta_sha256", "changed_paths"))
def test_matching_forged_review_callback_cannot_hide_a_bad_delta(
    monkeypatch, field,
):
    receipt = _receipt()
    object.__setattr__(
        receipt, field,
        "0" * 64 if field == "delta_sha256" else ("foreign.path",),
    )
    with pytest.raises(mod.DetachedPacketDeltaRejected, match="digest disagrees"):
        _check(monkeypatch, receipt)
