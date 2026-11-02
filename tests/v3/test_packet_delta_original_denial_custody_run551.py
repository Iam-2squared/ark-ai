"""Passive V3 packet deltas cannot adopt a replaced False-only authority."""

from __future__ import annotations

import pytest

from ark.learning import authorization_packet_delta_review as mod


def _review():
    return mod.review_unapproved_packet_delta(
        {"phase": {"name": "before"}},
        {"phase": {"name": "after"}},
        object(), object(),
        retained_old_file_sha256="a" * 64,
        retained_new_file_sha256="b" * 64,
    )


@pytest.mark.parametrize("flag", (
    "external_compute_authorized", "candidate_generation_authorized",
    "protected_evaluation_authorized", "main_merge_authorized",
))
def test_false_only_preinstalled_denial_descriptor_is_rejected_before_io(
    monkeypatch, flag,
):
    calls = []

    def callback(self):
        calls.append(self)
        return False

    monkeypatch.setattr(mod.ReviewPacketDelta, flag, property(callback))

    def should_not_verify(*args, **kwargs):
        raise AssertionError("packet-file verification must not begin")

    monkeypatch.setattr(
        mod, "verify_local_authorization_packet_file", should_not_verify,
    )
    with pytest.raises(mod.ReviewPacketDeltaRejected, match="descriptor changed"):
        _review()
    assert calls == []


def _mock_files(monkeypatch):
    # Unit-only stub: existing integration tests perform actual local file
    # readbacks. These snapshots are intentionally NOT executable approvals.
    monkeypatch.setattr(
        mod, "verify_local_authorization_packet_file",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        mod, "build_preflight_authorization_packet",
        lambda snapshot: snapshot,
    )


def test_reentrant_leaf_comparison_cannot_replace_last_denial(monkeypatch):
    _mock_files(monkeypatch)
    native = mod._leaf_bytes
    calls = []

    def altered(value):
        leaves = native(value)
        calls.append(1)
        if len(calls) == 2:
            monkeypatch.setattr(
                mod.ReviewPacketDelta, "main_merge_authorized",
                property(lambda self: False),
            )
        return leaves

    monkeypatch.setattr(mod, "_leaf_bytes", altered)
    with pytest.raises(mod.ReviewPacketDeltaRejected, match="changed"):
        _review()
    assert len(calls) == 2


def test_unmodified_synthetic_comparison_stays_non_authorizing(monkeypatch):
    _mock_files(monkeypatch)
    result = _review()
    assert result.changed_paths == ("phase.name",)
    assert result.external_compute_authorized is False
    assert result.candidate_generation_authorized is False
    assert result.protected_evaluation_authorized is False
    assert result.main_merge_authorized is False
