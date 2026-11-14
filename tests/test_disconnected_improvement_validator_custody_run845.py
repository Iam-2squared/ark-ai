"""Free-only ARK proposal drafts must not call injected local validators."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_improvement_proposal as proposal


def _proposal() -> proposal.ImprovementProposalInput:
    return proposal.ImprovementProposalInput(
        issue_id="memory.integrity",
        affected_component="planner",
        change_class="TEST_HARDENING",
        policy_revision=1,
        owner_digest="a" * 64,
        namespace_digest="b" * 64,
        source_digests=("c" * 64, "d" * 64),
    )


@pytest.mark.parametrize("helper", ("_name", "_sha"))
def test_rebound_helper_rejected_before_any_private_digest(
    monkeypatch: pytest.MonkeyPatch, helper: str,
) -> None:
    calls = []

    def attacker(value: object) -> str:
        calls.append(value)
        raise AssertionError("proposal validator substitution was invoked")

    monkeypatch.setattr(proposal, helper, attacker)
    with pytest.raises(proposal.DisconnectedImprovementRejected, match="protocol"):
        proposal.draft_disconnected_improvements((_proposal(),))
    assert calls == []


@pytest.mark.parametrize("field,bad", (
    ("issue_id", "x" * 65),
    ("affected_component", "x" * 100_000),
    ("owner_digest", "a" * 65),
    ("namespace_digest", "b" * 100_000),
    ("owner_digest", "a" * 63 + "\ud800"),
    ("source_digests", ("c" * 63, "d" * 64)),
))
def test_noncanonical_identifiers_never_create_proposals(field: str, bad: object) -> None:
    with pytest.raises(proposal.DisconnectedImprovementRejected):
        proposal.draft_disconnected_improvements(
            (replace(_proposal(), **{field: bad}),)
        )


def test_exact_proposal_identity_is_stable_and_grants_no_authority() -> None:
    item = _proposal()
    reversed_sources = replace(item, source_digests=tuple(reversed(item.source_digests)))
    one = proposal.draft_disconnected_improvements((item, reversed_sources))
    assert len(one) == 1
    assert one[0].occurrences == 2
    assert one[0].evidence_count == 2
    assert one[0].code_change_authorized is False
    assert one[0].training_authorized is False
    assert one[0].candidate_promotion_authorized is False
    assert one[0].protected_evaluation_opened is False
