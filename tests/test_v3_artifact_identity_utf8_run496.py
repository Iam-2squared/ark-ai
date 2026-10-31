"""Offline V3 lineage identity bytes must be deterministic and bounded.

No weights, model loading, Candidate creation, or external compute.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.learning.lineage import ArtifactIdentity, CandidateLineage


def _artifact():
    return ArtifactIdentity("model", "local.gguf", "a" * 64, 100, "rev-1")


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("kind", "model\x7f"),
        ("path", "local.gguf\x7f"),
        ("tool_revision", "rev-1\x7f"),
        ("path", "name" + chr(0xD800)),
        ("kind", "あ" * 1400),
        ("path", "あ" * 1400),
        ("tool_revision", "あ" * 1400),
    ),
)
def test_artifact_identity_rejects_invalid_or_overbudget_utf8(field, value):
    artifact = replace(_artifact(), **{field: value})
    with pytest.raises(ValueError, match="artifact identity"):
        artifact.validate()


def test_exact_byte_boundary_accepts_valid_unicode_but_no_authority():
    artifact = replace(_artifact(), path="あ" * 1365)
    artifact.validate()
    assert len(artifact.path.encode("utf-8")) == 4095


def test_canonical_lineage_rejects_bad_nested_artifact_without_weights():
    ordinary = _artifact()
    bad = replace(ordinary, path="artifact" + chr(0xD800))
    lineage = CandidateLineage(
        ordinary, ordinary, ordinary, ordinary, bad, ordinary,
    )
    with pytest.raises(ValueError, match="artifact identity"):
        lineage.canonical_bytes()
