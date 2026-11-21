"""Bound disconnected V3 digest identities without authorizing execution.

These are numerical, synthetic local fixtures only: no candidate, GPU,
training, external provider, protected evaluation, or approval is touched.
"""

import pytest

from ark import v3_detached_preflight_crossbind as module


def _review(snapshot_digest: str, evidence_digest: str) -> module.DetachedV3PreflightReview:
    snapshot = module.DetachedV3Snapshot(
        device="fixture-device", capacity_gib=8.0,
        tokenizer_probe_sha256=snapshot_digest,
        wall_clock_timeout_minutes=10,
    )
    evidence = module.DetachedV3Evidence(
        device="fixture-device", reported_capacity_gib=8.0,
        tokenizer_probe_sha256=evidence_digest,
        peak_vram_mib=128.0, peak_reserved_vram_mib=256.0,
        wall_seconds=3.0,
    )
    return module.review_detached_v3_preflight(snapshot, evidence)


@pytest.mark.parametrize("side", ("snapshot", "evidence"))
@pytest.mark.parametrize(
    "bad", ("a" * 65, "a" * 65536, "A" * 64, "é" * 64),
)
def test_unbounded_or_noncanonical_digest_denied(
    side: str, bad: str,
) -> None:
    snapshot = bad if side == "snapshot" else "a" * 64
    evidence = bad if side == "evidence" else "a" * 64
    with pytest.raises(
        module.DetachedV3PreflightRejected,
        match="invalid V3 tokenizer probe digest",
    ):
        _review(snapshot, evidence)


def test_exact_digest_still_returns_non_authorizing_review() -> None:
    result = _review("a" * 64, "a" * 64)
    assert len(result.digest) == 64
    assert result.paid_compute_authorized is False
    assert result.training_authorized is False
    assert result.candidate_promotion_authorized is False
    assert result.independent_provenance_verified is False
