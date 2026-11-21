"""Detached unapproved packet review retains both snapshot carrier epochs.

The producer callback here is intentionally fake; these are passive synthetic
mutation probes, not evidence of files, human approval, compute or Candidate.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.learning import authorization_packet_delta_recheck as mod
from ark.learning import authorization_packet_delta_review as base
from ark.learning.execution import canonical_json


def _retained():
    old, new, paths = "a" * 64, "b" * 64, ("synthetic.field",)
    digest = hashlib.sha256(
        mod._DOMAIN + canonical_json((old, new, paths)),
    ).hexdigest()
    return base.ReviewPacketDelta(old, new, paths, digest)


def _call(monkeypatch, old, new, callback):
    receipt = _retained()
    monkeypatch.setattr(mod, "review_unapproved_packet_delta", callback)
    return mod.verify_detached_unapproved_packet_delta(
        receipt, old, new, object(), object(),
        retained_old_file_sha256="a" * 64,
        retained_new_file_sha256="b" * 64,
    )


@pytest.mark.parametrize("which", ("old", "new"))
@pytest.mark.parametrize("mutation", ("different", "equal_mapping"))
def test_reentrant_review_cannot_rewrite_caller_snapshot(
    monkeypatch, which, mutation,
):
    old = {"nested": {"fixture": "value"}}
    new = {"nested": {"fixture": "different"}}
    target = old if which == "old" else new
    called = []

    def reentrant_fake(*args, **kwargs):
        called.append(True)
        if mutation == "different":
            target["nested"]["fixture"] = "changed"
        else:
            target["nested"] = dict(target["nested"])
        return _retained()

    with pytest.raises(mod.DetachedPacketDeltaRejected, match="snapshot changed"):
        _call(monkeypatch, old, new, reentrant_fake)
    assert called == [True]


@pytest.mark.parametrize("bad", ([], object()))
def test_nonexact_snapshot_type_is_rejected_before_review(monkeypatch, bad):
    calls = []

    def fake(*args, **kwargs):
        calls.append(True)
        return _retained()

    with pytest.raises(mod.DetachedPacketDeltaRejected, match="exact"):
        _call(monkeypatch, bad, {}, fake)
    assert calls == []


def test_unchanged_detached_mock_still_remains_non_authorizing(monkeypatch):
    old = {"nested": {"fixture": "value"}}
    new = {"nested": {"fixture": "different"}}
    receipt = _retained()
    monkeypatch.setattr(
        mod, "review_unapproved_packet_delta",
        lambda *args, **kwargs: receipt,
    )
    assert mod.verify_detached_unapproved_packet_delta(
        receipt, old, new, object(), object(),
        retained_old_file_sha256="a" * 64,
        retained_new_file_sha256="b" * 64,
    ) is None
    assert receipt.external_compute_authorized is False
    assert receipt.candidate_generation_authorized is False
    assert receipt.protected_evaluation_authorized is False
    assert receipt.main_merge_authorized is False
