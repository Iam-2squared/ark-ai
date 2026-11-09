"""Fail-closed synthetic multi-store epochs before any substituted codec sees claims.

The detached vector grants no authority, provenance or coherent DB snapshot.
No private store is opened and no real action or evaluation is performed.
"""

from __future__ import annotations

import re

import pytest

from ark import disconnected_epoch_vector as module


def _claims():
    return (
        module.DisconnectedStoreEpoch(
            store_id="memory", incarnation_sha256="a" * 64,
            schema_sha256="b" * 64, generation=1, event_count=1,
            event_tail_sha256="c" * 64, state_sha256="d" * 64,
            logical_time_ns=20,
        ),
    )


def _replace_helper(monkeypatch, dependency):
    def unsafe(*_args, **_kwargs):
        pytest.fail("substituted epoch metadata callback was executed")

    if dependency == "hashlib":
        monkeypatch.setattr(module, "hashlib", object())
    elif dependency == "json":
        monkeypatch.setattr(module, "json", object())
    elif dependency == "sha256":
        monkeypatch.setattr(module.hashlib, "sha256", unsafe)
    elif dependency == "dumps":
        monkeypatch.setattr(module.json, "dumps", unsafe)
    elif dependency == "sha_pattern":
        monkeypatch.setattr(module, "_SHA", re.compile(".*"))
    elif dependency == "store_pattern":
        monkeypatch.setattr(module, "_STORE", re.compile(".*"))
    elif dependency == "domain":
        monkeypatch.setattr(module, "_DOMAIN", b"unreviewed-epoch-domain\\0")
    elif dependency == "store_limit":
        monkeypatch.setattr(module, "_MAX_STORES", 17)
    elif dependency == "integer_limit":
        monkeypatch.setattr(module, "_MAX_INTEGER", 2**64)
    else:
        pytest.fail("unknown dependency")


@pytest.mark.parametrize("dependency", (
    "hashlib", "json", "sha256", "dumps", "sha_pattern",
    "store_pattern", "domain", "store_limit", "integer_limit",
))
def test_capture_rejects_substituted_epoch_dependencies_before_read(monkeypatch, dependency):
    claims = _claims()
    _replace_helper(monkeypatch, dependency)
    with pytest.raises(module.EpochVectorRejected, match="dependencies changed"):
        module.capture_disconnected_epoch_vector(claims)


@pytest.mark.parametrize("dependency", (
    "hashlib", "json", "sha256", "dumps", "sha_pattern",
    "store_pattern", "domain", "store_limit", "integer_limit",
))
def test_review_rejects_substituted_epoch_dependencies_before_read(monkeypatch, dependency):
    previous = module.capture_disconnected_epoch_vector(_claims())
    observed = module.capture_disconnected_epoch_vector(_claims())
    _replace_helper(monkeypatch, dependency)
    with pytest.raises(module.EpochVectorRejected, match="dependencies changed"):
        module.review_disconnected_epoch_progress(previous, observed)


def test_original_helpers_still_generate_bounded_inert_consistency_hint():
    retained = module.capture_disconnected_epoch_vector(_claims())
    observed = module.capture_disconnected_epoch_vector(_claims())
    assert module.review_disconnected_epoch_progress(retained, observed) is observed
    assert observed.coherent_snapshot_proven is False
    assert observed.dispatch_authorized is False
    assert len(observed.digest) == 64
