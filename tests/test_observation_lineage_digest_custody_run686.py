"""Offline observation lineage refuses a forged digest implementation.

All content SHA values are synthetic fixture metadata. Passing this review
does not authenticate sources, authorize sensors, disclose data or dispatch.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.observation_lineage_review as lineage
from ark.observations import ObservationEnvelope, ObservationKind


def _review():
    envelope = ObservationEnvelope(
        ObservationKind.TEXT, "fixture-source", "fixture-adapter",
        "private-fixture", 100, "a" * 64,
    )
    return lineage.review_synthetic_observation_lineage(
        (envelope,), privacy_scope="private-fixture", now_ms=110,
        max_age_ms=20,
    )


@pytest.mark.parametrize(
    "replacement",
    ("hashlib_module", "json_module", "sha256", "dumps", "equal_domain"),
)
def test_digest_replacement_is_rejected_before_any_private_window(
    monkeypatch, replacement,
):
    hits = []

    def untrusted(*args, **kwargs):
        hits.append(replacement)
        raise AssertionError("untrusted hashing/serialization executed")

    if replacement == "hashlib_module":
        monkeypatch.setattr(
            lineage, "hashlib", SimpleNamespace(sha256=untrusted),
        )
    elif replacement == "json_module":
        monkeypatch.setattr(
            lineage, "json", SimpleNamespace(dumps=untrusted),
        )
    elif replacement == "sha256":
        monkeypatch.setattr(lineage.hashlib, "sha256", untrusted)
    elif replacement == "dumps":
        monkeypatch.setattr(lineage.json, "dumps", untrusted)
    else:
        # Equal VALUE with different byte-object ID is not the original domain.
        replacement_domain = bytes(bytearray(lineage._LINEAGE_DOMAIN))
        assert replacement_domain == lineage._LINEAGE_DOMAIN
        assert replacement_domain is not lineage._LINEAGE_DOMAIN
        monkeypatch.setattr(lineage, "_LINEAGE_DOMAIN", replacement_domain)

    def forbidden_window(*args, **kwargs):
        raise AssertionError("private window read before digest custody")

    monkeypatch.setattr(lineage, "ObservationWindowReview", forbidden_window)
    with pytest.raises(
        lineage.SyntheticObservationLineageRejected,
        match="digest implementation changed",
    ):
        _review()
    assert hits == []


def test_clean_multi_step_lineage_remains_deterministic_and_deny_only():
    root = ObservationEnvelope(
        ObservationKind.TEXT, "fixture", "text", "private-fixture",
        100, "a" * 64,
    )
    child = ObservationEnvelope(
        ObservationKind.TRANSCRIPT, "fixture", "transcript", "private-fixture",
        105, "b" * 64, root.content_sha256,
    )
    def run(rows):
        return lineage.review_synthetic_observation_lineage(
            rows, privacy_scope="private-fixture", now_ms=110,
            max_age_ms=20,
        )

    first = run((root, child))
    assert first == run((child, root))
    assert first.observation_count == 2
    assert first.media_capture_authorized is False
    assert first.disclosure_authorized is False
    assert first.dispatch_authorized is False
