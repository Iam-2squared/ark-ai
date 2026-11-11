"""Proposal-only ARK self-improvement identity has no action authority."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency import disconnected_improvement_proposal as proposal

_A = "a" * 64
_B = "b" * 64
_C = "c" * 64
_D = "d" * 64


def _input(
    *,
    sources=(_C, _D),
    owner=_A,
    namespace=_B,
):
    return proposal.ImprovementProposalInput(
        "planner.failure", "ark.agency.planner",
        "TEST_HARDENING", 1, owner, namespace, sources,
    )


def test_order_independent_source_digest_and_idempotent_proposal_identity():
    original = _input()
    reversed_sources = _input(sources=(_D, _C))
    first = proposal.draft_disconnected_improvements((original,))
    reordered = proposal.draft_disconnected_improvements((reversed_sources,))
    assert first == reordered
    duplicate = proposal.draft_disconnected_improvements((
        original, reversed_sources, original,
    ))
    assert len(duplicate) == 1
    assert duplicate[0].proposal_id == first[0].proposal_id
    assert duplicate[0].evidence_count == 2
    assert duplicate[0].occurrences == 3
    assert duplicate[0].code_change_authorized is False
    assert duplicate[0].training_authorized is False
    assert duplicate[0].candidate_promotion_authorized is False
    assert duplicate[0].protected_evaluation_opened is False


def test_owner_namespace_revision_change_class_and_evidence_partition_ids():
    base = _input()
    alternatives = (
        replace(base, owner_digest=_B),
        replace(base, namespace_digest=_A),
        replace(base, policy_revision=2),
        replace(base, change_class="FAILURE_INVESTIGATION"),
        replace(base, affected_component="ark.agency.registry"),
        replace(base, source_digests=(_C,)),
    )
    outputs = proposal.draft_disconnected_improvements(
        (base, *alternatives),
    )
    assert len(outputs) == 7
    assert len({item.proposal_id for item in outputs}) == 7
    assert all(item.occurrences == 1 for item in outputs)


@pytest.mark.parametrize(("field", "invalid"), (
    ("issue_id", "planner failure details"),
    ("issue_id", "../private"),
    ("issue_id", ""),
    ("affected_component", "Private memory text"),
    ("affected_component", "x" * 100),
    ("change_class", "RUN_TRAINING"),
    ("change_class", "PROMOTE_CANDIDATE"),
    ("change_class", "WRITE_CODE"),
    ("policy_revision", True),
    ("policy_revision", 0),
    ("policy_revision", -1),
    ("policy_revision", 2**40),
    ("owner_digest", _A.upper()),
    ("namespace_digest", "unhashed"),
    ("source_digests", ()),
    ("source_digests", (_C, _C)),
    ("source_digests", (_C, "private-text")),
    ("source_digests", (_C,) * 33),
    ("source_digests", [_C]),
))
def test_invalid_or_unsafe_proposal_is_rejected(field, invalid):
    with pytest.raises(proposal.DisconnectedImprovementRejected):
        proposal.draft_disconnected_improvements((
            replace(_input(), **{field: invalid}),
        ))


def test_nonexact_container_and_budget_are_rejected():
    p = _input()
    with pytest.raises(proposal.DisconnectedImprovementRejected):
        proposal.draft_disconnected_improvements([p])
    with pytest.raises(proposal.DisconnectedImprovementRejected):
        proposal.draft_disconnected_improvements(())
    with pytest.raises(proposal.DisconnectedImprovementRejected):
        proposal.draft_disconnected_improvements((p,) * 257)


@pytest.mark.parametrize("denial", (
    "code_change_authorized", "training_authorized",
    "candidate_promotion_authorized", "protected_evaluation_opened",
))
def test_replaced_denial_descriptor_cannot_be_consulted(monkeypatch, denial):
    touched = []

    def unsafe(_self):
        touched.append(denial)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(proposal.ImprovementProposalDraft, denial, property(unsafe))
        with pytest.raises(proposal.DisconnectedImprovementRejected, match="protocol"):
            proposal.draft_disconnected_improvements((_input(),))
    assert touched == []
