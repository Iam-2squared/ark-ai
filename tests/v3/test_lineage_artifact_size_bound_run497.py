"""V3 evidence sizes must be finite, exact SQLite-compatible byte counts."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.learning.lineage import ArtifactIdentity, CandidateLineage


def identity(*, size: int = 1) -> ArtifactIdentity:
    return ArtifactIdentity("base", "local/base.bin", "a" * 64, size, "b" * 40)


@pytest.mark.parametrize("size", (2**63, 2**64, 10**100, -1))
def test_artifact_bytes_outside_signed_64_bit_budget_rejected(size):
    with pytest.raises(ValueError, match="byte size"):
        identity(size=size).validate()


def test_largest_supported_byte_count_is_only_a_metadata_claim():
    entry = identity(size=2**63 - 1)
    entry.validate()
    assert entry.bytes == 2**63 - 1


def test_lineage_rejects_oversized_nested_artifact_without_producing_evidence():
    entry = identity()
    lineage = CandidateLineage(entry, entry, entry, entry, entry, entry)
    with pytest.raises(ValueError, match="byte size"):
        replace(lineage, adapter=replace(entry, bytes=2**63)).canonical_bytes()
