"""Inert atomic recovery results cannot acquire authority via monkeypatches.

The reviewer must fail on substituted result descriptors before reaching
private SQLite, even if a forged descriptor would return a harmless value.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

import ark.agency.disconnected_atomic_binding_snapshot_review as binding


@pytest.mark.parametrize(
    "attribute",
    (
        "occurrence_id",
        "local_state",
        "retained_count",
        "local_binding_matches",
        "binding_proven",
        "tool_dispatch_authorized",
        "automatic_replay_authorized",
        "external_effect_proven",
        "independent_custody_proven",
        "manual_review_required",
        "__init__",
        "__getattribute__",
        "__getattr__",
    ),
)
def test_changed_result_definition_denied_before_private_inputs(
    attribute: str,
) -> None:
    # Monkeypatch's inherited-special-method restoration would introduce a
    # new own class attribute. Restore the exact original class dictionary.
    cls = binding.AtomicBindingSnapshotReview
    missing = object()
    original = vars(cls).get(attribute, missing)
    try:
        setattr(cls, attribute, property(lambda self: False))
        with pytest.raises(
            binding.AtomicBindingSnapshotRejected,
            match="reader definition changed",
        ):
            binding.review_registered_atomic_binding_snapshot(
                None, None, None, None, occurrence_id="synthetic-invalid",
            )
    finally:
        if original is missing:
            delattr(cls, attribute)
        else:
            setattr(cls, attribute, original)


def test_new_constructor_substitution_denied_in_isolated_process() -> None:
    # Setting __new__ on a Python slotted dataclass may irreversibly alter
    # the live type's construction slot even after delattr; isolate the
    # monkeypatch in a child interpreter so subsequent tests stay pristine.
    program = textwrap.dedent(
        """
        import ark.agency.disconnected_atomic_binding_snapshot_review as binding

        cls = binding.AtomicBindingSnapshotReview
        cls.__new__ = property(lambda self: False)
        try:
            binding.review_registered_atomic_binding_snapshot(
                None, None, None, None, occurrence_id="synthetic-invalid",
            )
        except binding.AtomicBindingSnapshotRejected as exc:
            assert "reader definition changed" in str(exc)
        else:
            raise AssertionError("untrusted constructor was not rejected")
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        check=False, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr


def test_result_class_alias_replacement_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(binding, "AtomicBindingSnapshotReview", object)
    with pytest.raises(
        binding.AtomicBindingSnapshotRejected,
        match="reader definition changed",
    ):
        binding.review_registered_atomic_binding_snapshot(
            None, None, None, None, occurrence_id="synthetic-invalid",
        )


@pytest.mark.parametrize(
    "local_state", ("ABSENT", "LOCAL_MATCH", "LOCAL_CONFLICT"),
)
def test_local_states_are_never_authorization(local_state: str) -> None:
    result = binding.AtomicBindingSnapshotReview(
        "occ_" + "a" * 64, local_state, 1,
    )
    assert result.local_binding_matches is (local_state == "LOCAL_MATCH")
    assert result.binding_proven is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_effect_proven is False
    assert result.independent_custody_proven is False
    assert result.manual_review_required is True
