"""Synthetic proposal identity carrier control plane: fail before ingress."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_improvement_proposal as mod


def _valid():
    return (mod.ImprovementProposalInput(
        issue_id="integrity", affected_component="planner",
        change_class="TEST_HARDENING", policy_revision=1,
        owner_digest="a" * 64, namespace_digest="b" * 64,
        source_digests=("c" * 64,),
    ),)


@pytest.mark.parametrize(("name", "replacement"), (
    ("_INPUT_FIELDS", ("issue_id",)),
    ("_OUTPUT_FIELDS", ("proposal_id",)),
    ("_DENIALS", ("training_authorized",)),
))
def test_changed_field_and_denial_names_are_rejected(monkeypatch, name, replacement):
    proposals = _valid()
    with monkeypatch.context() as patch:
        patch.setattr(mod, name, replacement)
        with pytest.raises(mod.DisconnectedImprovementRejected, match="protocol"):
            mod.draft_disconnected_improvements(proposals)
    assert len(mod.draft_disconnected_improvements(proposals)) == 1


@pytest.mark.parametrize("carrier", ("ImprovementProposalInput", "ImprovementProposalDraft"))
def test_changed_carrier_initializer_rejected_before_draft(monkeypatch, carrier):
    proposals = _valid()
    cls = getattr(mod, carrier)
    seen = []

    def poisoned(*_args, **_kwargs):
        seen.append(True)
        raise AssertionError("constructor should not run")

    with monkeypatch.context() as patch:
        patch.setattr(cls, "__init__", poisoned)
        with pytest.raises(mod.DisconnectedImprovementRejected, match="protocol"):
            mod.draft_disconnected_improvements(proposals)
    assert not seen


@pytest.mark.parametrize("carrier", ("ImprovementProposalInput", "ImprovementProposalDraft"))
def test_added_carrier_getattr_rejected_and_restored(monkeypatch, carrier):
    proposals = _valid()
    cls = getattr(mod, carrier)
    assert "__getattr__" not in vars(cls)
    with monkeypatch.context() as patch:
        patch.setattr(cls, "__getattr__", lambda *_args: True, raising=False)
        with pytest.raises(mod.DisconnectedImprovementRejected, match="protocol"):
            mod.draft_disconnected_improvements(proposals)
    assert "__getattr__" not in vars(cls)


def test_valid_identity_is_non_authoritative_and_stable():
    left = mod.draft_disconnected_improvements(_valid())
    right = mod.draft_disconnected_improvements(_valid())
    assert left == right
    assert left[0].code_change_authorized is False
    assert left[0].candidate_promotion_authorized is False
    assert left[0].training_authorized is False
    assert left[0].protected_evaluation_opened is False
