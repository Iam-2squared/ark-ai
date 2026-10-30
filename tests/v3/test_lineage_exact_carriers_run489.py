"""Validation-only V3 lineage: exact immutable evidence carriers; no training."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.learning.lineage import ArtifactIdentity, CandidateLineage


class StrCarrier(str):
    def strip(self, *args, **kwargs):
        raise AssertionError("unsafe str subclass callback must not run")


def artifact(kind="base", path="local/base.bin", sha256="a" * 64,
             bytes=7, tool_revision="b" * 40):
    return ArtifactIdentity(kind, path, sha256, bytes, tool_revision)


def lineage():
    return CandidateLineage(
        artifact(kind="base"), artifact(kind="adapter"),
        artifact(kind="merged"), artifact(kind="f32"),
        artifact(kind="candidate-q4"), artifact(kind="baseline-q4"),
    )


def test_valid_lineage_is_deterministic_and_nonexecuting():
    value = lineage()
    value.validate()
    assert value.sha256 == value.sha256
    assert value.canonical_bytes().endswith(b"\n")


@pytest.mark.parametrize("field,bad", [
    ("kind", None), ("kind", True), ("kind", 22),
    ("kind", StrCarrier("base")),
    ("path", StrCarrier("local/base.bin")),
    ("tool_revision", StrCarrier("a" * 40)),
    ("path", "local\\x00binary"),
    ("path", "line\nfeed"),
    ("path", "x" * 4097),
    ("kind", "  "),
    ("tool_revision", ""),
])
def test_artifact_text_fields_require_exact_inert_strings(field, bad):
    value = replace(artifact(), **{field: bad})
    with pytest.raises(ValueError, match="identity fields"):
        value.validate()


@pytest.mark.parametrize("sha", [
    None, True, "A" * 64, "a" * 63,
    StrCarrier("a" * 64),
])
def test_artifact_sha_rejects_invalid_exact_types(sha):
    with pytest.raises(ValueError, match="SHA-256"):
        replace(artifact(), sha256=sha).validate()


@pytest.mark.parametrize("size", [True, 0, -1, 1.0, "12"])
def test_artifact_sizes_do_not_accept_bool_or_coercions(size):
    with pytest.raises(ValueError, match="byte size"):
        replace(artifact(), bytes=size).validate()


@pytest.mark.parametrize("field,bad", [
    ("schema_version", True),
    ("schema_version", 1.0),
    ("schema_version", "1"),
    ("quantization", StrCarrier("Q4_K_M")),
    ("quantization", 0),
    ("quantization", "Q8_0"),
])
def test_lineage_schema_and_quantization_are_exact(field, bad):
    with pytest.raises(ValueError, match="schema/quantization"):
        replace(lineage(), **{field: bad}).validate()


@pytest.mark.parametrize("field", [
    "base", "adapter", "merged_hf", "gguf_f32",
    "gguf_q4km", "paired_base_q4km",
])
def test_all_six_artifact_slots_require_original_identity_type(field):
    forged = replace(lineage(), **{field: {"kind": "base"}})
    with pytest.raises(ValueError, match="exact artifact lineage"):
        forged.validate()


def test_lineage_still_requires_identical_paired_quantizer_revision():
    forged = replace(
        lineage(),
        paired_base_q4km=replace(artifact(), tool_revision="c" * 40),
    )
    with pytest.raises(ValueError, match="revision mismatch"):
        forged.validate()
