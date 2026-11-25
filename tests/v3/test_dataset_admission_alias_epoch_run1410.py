"""Run1410: V3 dataset admission pins original type and validator aliases."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

import ark.learning.dataset as dataset_module


def test_joint_type_and_validator_alias_rebinding_is_denied_before_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    @dataclass(frozen=True)
    class ReplacementCandidate:
        candidate_id: str
        source_type: str
        source_reference: str
        input: str
        model_response: str
        evaluation: str
        approved_target: str
        rejection_reason: str
        provenance: str
        created_at: str
        reviewer: str
        source_sha256: str
        rights: str
        approved: bool
        independent: bool
        split: str
        group: str
        schema_version: int = 1

        def validate(self) -> None:
            calls.append("replacement candidate validator")

    @dataclass(frozen=True)
    class ReplacementGuard:
        protected_inputs: tuple[str, ...]
        protected_targets: tuple[str, ...]
        reference_markers: tuple[str, ...] = (
            "ark-v2-foundation", "evidence/v2", "evaluation/",
        )

        def reason(self, _item: object) -> None:
            calls.append("replacement contamination guard")
            return None

    candidate = ReplacementCandidate(
        candidate_id="candidate-a",
        source_type="human_authored",
        source_reference="synthetic://candidate-a",
        input="synthetic prompt",
        model_response="synthetic response",
        evaluation="synthetic evaluation",
        approved_target="synthetic target",
        rejection_reason="",
        provenance="synthetic provenance",
        created_at="2026-09-10T00:00:00+00:00",
        reviewer="fixture-reviewer",
        source_sha256="a" * 64,
        rights="owned",
        approved=True,
        independent=True,
        split="train",
        group="group-a",
    )
    guard = ReplacementGuard((), ())

    # Rebind the public names and all private "original" aliases together.
    # The previous pairwise checks accepted this self-consistent replacement.
    monkeypatch.setattr(dataset_module, "LearningCandidate", ReplacementCandidate)
    monkeypatch.setattr(
        dataset_module, "_ORIGINAL_LEARNING_CANDIDATE_TYPE", ReplacementCandidate,
    )
    monkeypatch.setattr(
        dataset_module,
        "_ORIGINAL_LEARNING_CANDIDATE_VALIDATE",
        ReplacementCandidate.validate,
    )
    monkeypatch.setattr(dataset_module, "ContaminationGuard", ReplacementGuard)
    monkeypatch.setattr(
        dataset_module, "_ORIGINAL_CONTAMINATION_GUARD_TYPE", ReplacementGuard,
    )
    monkeypatch.setattr(
        dataset_module,
        "_ORIGINAL_CONTAMINATION_GUARD_REASON",
        ReplacementGuard.reason,
    )

    with pytest.raises(
        ValueError,
        match="dataset admission policy implementation changed",
    ):
        dataset_module.build_dataset([candidate], guard)

    assert calls == []


def test_equal_valued_admission_epoch_replacement_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = dataset_module._ORIGINAL_DATASET_ADMISSION_EPOCH
    forged = tuple([*original])
    assert forged == original
    assert forged is not original
    monkeypatch.setattr(dataset_module, "_ORIGINAL_DATASET_ADMISSION_EPOCH", forged)

    with pytest.raises(
        ValueError,
        match="dataset admission policy implementation changed",
    ):
        dataset_module.build_dataset([], dataset_module.ContaminationGuard((), ()))
