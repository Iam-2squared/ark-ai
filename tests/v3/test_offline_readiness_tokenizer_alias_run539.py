"""Pending tokenizer revision identities remain visible in passive V3 inventory.

The paths are only syntactic review hints; none are authorization to fetch
models, run an optimizer, provision compute, or open protected evaluation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ark.learning.offline_readiness_inventory import inventory_unapproved_v3_readiness

_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


@pytest.mark.parametrize(
    "base_revision,tokenizer_revision,expected_tokenizer,expected_count",
    (
        ("UNRESOLVED", "SAME_AS_BASE", True, 26),
        ("USER_APPROVAL_REQUIRED", "SAME_AS_BASE", True, 26),
        ("a" * 40, "UNRESOLVED", True, 25),
        ("a" * 40, "USER_APPROVAL_REQUIRED", True, 25),
        ("a" * 40, "SAME_AS_BASE", False, 24),
        ("UNRESOLVED", "b" * 40, False, 25),
    ),
)
def test_tokenizer_revision_is_tracked_independently_of_base_material(
    base_revision, tokenizer_revision, expected_tokenizer, expected_count,
):
    snapshot = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    snapshot["base"]["revision"] = base_revision
    snapshot["tokenizer"]["revision"] = tokenizer_revision
    result = inventory_unapproved_v3_readiness(snapshot)
    assert ("tokenizer.revision" in result.unresolved_paths) is expected_tokenizer
    assert result.unresolved_count == expected_count
    assert result.unresolved_paths == tuple(sorted(set(result.unresolved_paths)))
    assert ("base.revision" in result.unresolved_paths) is (
        base_revision in ("UNRESOLVED", "USER_APPROVAL_REQUIRED")
    )
    canonical = json.dumps(
        snapshot, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    assert result.snapshot_sha256 == hashlib.sha256(canonical).hexdigest()
    assert result.external_compute_authorized is False
    assert result.candidate_generation_authorized is False
    assert result.protected_evaluation_authorized is False
    assert result.promotion_authorized is False
