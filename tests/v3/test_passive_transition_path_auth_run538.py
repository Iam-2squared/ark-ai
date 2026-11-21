"""Unapproved V3 progress cannot be forged by re-labelling shape callback paths."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ark.learning import offline_readiness_transition as transition

_TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(_TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("field,value", (
    ("unresolved_paths", ()),
    ("invalid_shape_paths", ("fictional.invalid",)),
    ("unresolved_paths", ("fictional.source",)),
))
def test_correct_snapshot_sha_does_not_validate_forged_categories(
    monkeypatch, field, value,
):
    native = transition.review_unapproved_v3_snapshot_shapes

    def forged(mapping):
        # Keep the real snapshot SHA, checked count and exact result class.
        return replace(native(mapping), **{field: value})

    monkeypatch.setattr(transition, "review_unapproved_v3_snapshot_shapes", forged)
    with pytest.raises(
        transition.PassiveTransitionRejected, match="path classification mismatch",
    ):
        transition.review_passive_readiness_transition(_snapshot(), _snapshot())


@pytest.mark.parametrize("misclassification", ("hide_invalid", "fake_repair"))
def test_invalid_identity_cannot_be_reclassified_as_readiness_progress(
    monkeypatch, misclassification,
):
    before, after = _snapshot(), _snapshot()
    after["export"]["converter_identity"] = "not-a-real-sha"
    native = transition.review_unapproved_v3_snapshot_shapes

    def forged(mapping):
        original = native(mapping)
        if mapping is after:
            if misclassification == "hide_invalid":
                return replace(original, invalid_shape_paths=())
            return replace(
                original,
                invalid_shape_paths=(),
                unresolved_paths=tuple(sorted((
                    *original.unresolved_paths, "export.converter_identity",
                ))),
            )
        return original

    monkeypatch.setattr(transition, "review_unapproved_v3_snapshot_shapes", forged)
    with pytest.raises(
        transition.PassiveTransitionRejected, match="path classification mismatch",
    ):
        transition.review_passive_readiness_transition(before, after)


def test_legitimate_alias_change_still_reports_syntax_only():
    before, after = _snapshot(), _snapshot()
    after["base"]["revision"] = "a" * 40
    result = transition.review_passive_readiness_transition(before, after)
    assert result.newly_plausible_paths == (
        "base.revision", "tokenizer.revision",
    )
    assert result.external_compute_authorized is False
    assert result.real_training_authorized is False
    assert result.protected_v2_authorized is False
    assert result.human_approval_verified is False
