"""Run1235: V3 dataset admission rejects callback-capable object carriers."""

from __future__ import annotations

import pytest

from ark.learning.dataset import (
    ContaminationGuard,
    LearningCandidate,
    build_dataset,
)


def _candidate(**overrides: object) -> LearningCandidate:
    values: dict[str, object] = {
        "candidate_id": "candidate-a",
        "source_type": "human_authored",
        "source_reference": "synthetic://candidate-a",
        "input": "synthetic prompt",
        "model_response": "synthetic response",
        "evaluation": "synthetic evaluation",
        "approved_target": "synthetic target",
        "rejection_reason": "",
        "provenance": "synthetic provenance",
        "created_at": "2026-09-10T00:00:00+00:00",
        "reviewer": "fixture-reviewer",
        "source_sha256": "a" * 64,
        "rights": "owned",
        "approved": True,
        "independent": True,
        "split": "train",
        "group": "group-a",
    }
    values.update(overrides)
    return LearningCandidate(**values)  # type: ignore[arg-type]


def _guard() -> ContaminationGuard:
    return ContaminationGuard((), ())


def test_candidate_list_subclass_is_rejected_before_iteration() -> None:
    class CallbackList(list):
        def __iter__(self):
            raise AssertionError("list subclass iterator must not run")

    with pytest.raises(ValueError, match="exact list"):
        build_dataset(CallbackList([_candidate()]), _guard())


def test_candidate_subclass_is_rejected_before_attribute_callbacks() -> None:
    class CallbackCandidate(LearningCandidate):
        def __getattribute__(self, name):
            raise AssertionError("candidate subclass callback must not run")

    hostile = CallbackCandidate(**vars(_candidate()))
    with pytest.raises(ValueError, match="exact LearningCandidate"):
        build_dataset([hostile], _guard())


def test_candidate_id_string_subclass_is_rejected_before_strip() -> None:
    class CallbackText(str):
        def strip(self, *args, **kwargs):
            raise AssertionError("string subclass callback must not run")

    with pytest.raises(ValueError, match="candidate ID must be an exact string"):
        build_dataset([_candidate(candidate_id=CallbackText("candidate-a"))], _guard())


def test_candidate_validation_rejects_string_subclasses_before_strip() -> None:
    class CallbackText(str):
        def strip(self, *args, **kwargs):
            raise AssertionError("string subclass callback must not run")

    candidate = _candidate(source_reference=CallbackText("synthetic://candidate-a"))
    with pytest.raises(ValueError, match="exact string"):
        candidate.validate()


def test_contamination_guard_subclass_is_rejected_before_policy_callback() -> None:
    class CallbackGuard(ContaminationGuard):
        def reason(self, item):
            raise AssertionError("guard subclass callback must not run")

    with pytest.raises(ValueError, match="exact ContaminationGuard"):
        build_dataset([_candidate()], CallbackGuard((), ()))


def test_guard_tuple_subclass_is_rejected_before_iteration() -> None:
    class CallbackTuple(tuple):
        def __iter__(self):
            raise AssertionError("tuple subclass iterator must not run")

    guard = _guard()
    object.__setattr__(guard, "protected_inputs", CallbackTuple(("protected",)))

    with pytest.raises(ValueError, match="exact immutable text tuples"):
        build_dataset([_candidate()], guard)


def test_direct_contamination_review_rejects_string_subclass_before_normalization() -> None:
    class CallbackText(str):
        def casefold(self):
            raise AssertionError("string subclass normalization callback must not run")

    candidate = _candidate()
    object.__setattr__(candidate, "input", CallbackText("synthetic prompt"))

    with pytest.raises(ValueError, match="exact candidate text"):
        _guard().reason(candidate)


def test_exact_candidates_keep_deterministic_dataset_bytes() -> None:
    first = _candidate(candidate_id="candidate-a", group="group-a")
    second = _candidate(
        candidate_id="candidate-b",
        input="another synthetic prompt",
        approved_target="another synthetic target",
        group="group-b",
        split="validation",
    )

    forward = build_dataset([first, second], _guard())
    reverse = build_dataset([second, first], _guard())

    assert forward == reverse
    assert forward.summary["accepted"] == 2
    assert forward.summary["train_examples"] == 1
    assert forward.summary["validation_examples"] == 1
