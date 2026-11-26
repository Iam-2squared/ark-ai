"""Free-only V3 crossbind validator custody, with no runtime or GPU access."""

from __future__ import annotations

import pytest

from ark import v3_detached_preflight_crossbind as review


def _synthetic():
    return (
        review.DetachedV3Snapshot("cuda:0", 12.0, "a" * 64, 20),
        review.DetachedV3Evidence(
            "cuda:0", 12.0, "a" * 64, 4096.0, 6144.0, 300.0,
        ),
    )


@pytest.mark.parametrize("helper", ("_numeric", "_device", "_digest"))
def test_replaced_validator_refused_before_private_metadata_or_callback(
    monkeypatch: pytest.MonkeyPatch, helper: str,
) -> None:
    calls: list[str] = []

    def forged(_value: object) -> object:
        calls.append(helper)
        raise AssertionError("rebound V3 validator executed")

    snapshot, evidence = _synthetic()
    with monkeypatch.context() as patch:
        patch.setattr(review, helper, forged)
        with pytest.raises(
            review.DetachedV3PreflightRejected, match="protocol changed",
        ):
            review.review_detached_v3_preflight(snapshot, evidence)
    assert calls == []


def test_unmodified_detached_review_does_not_prove_provenance_or_payment() -> None:
    result = review.review_detached_v3_preflight(*_synthetic())
    assert result.checks == (
        "device", "capacity", "tokenizer_probe", "peak_vram_order",
        "wall_clock_budget",
    )
    assert len(result.digest) == 64
    assert result.independent_provenance_verified is False
    assert result.training_authorized is False
    assert result.paid_compute_authorized is False
    assert result.candidate_promotion_authorized is False
