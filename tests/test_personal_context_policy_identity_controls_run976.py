"""Personal Context policy revisions reject ambiguous control-bearing IDs.

The public Memory v1 contract is unchanged; no real private context, consent,
network, tools, credentials or durable profile data are used.
"""

from __future__ import annotations

import pytest

from ark.personal_context_review import ContextSelectionPolicy


@pytest.mark.parametrize(
    ("control", "diagnostic"),
    (
        ("\n", "control delimiter"),
        ("\t", "control delimiter"),
        ("\x7f", "control delimiter"),
        ("\u009b", "Unicode formatting control"),
        ("\u202e", "Unicode formatting control"),
        ("\u2066", "Unicode formatting control"),
        ("\u200b", "Unicode formatting control"),
        ("\u2028", "Unicode formatting control"),
        ("\ufeff", "Unicode formatting control"),
    ),
)
@pytest.mark.parametrize("reflected", (False, True))
def test_context_revision_controls_rejected_even_after_reflection(
    control: str, diagnostic: str, reflected: bool,
) -> None:
    value = "policy" + control + "spoof"
    if reflected:
        policy = ContextSelectionPolicy(3, 2, "safe_v1")
        object.__setattr__(policy, "policy_revision", value)
        with pytest.raises(ValueError, match=diagnostic):
            policy.__post_init__()
    else:
        with pytest.raises(ValueError, match=diagnostic):
            ContextSelectionPolicy(3, 2, value)


def test_context_policy_accepts_clean_multilingual_revision() -> None:
    policy = ContextSelectionPolicy(
        total_limit=3,
        per_namespace_limit=2,
        policy_revision="改訂_日本語_v1",
    )
    policy.__post_init__()
    assert policy.policy_revision == "改訂_日本語_v1"
    assert policy.total_limit == 3
