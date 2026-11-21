"""Synthetic proactive attention constructor checks must never invoke __eq__.

No notifications, trusted clock, consent or external tool is involved.
"""

from __future__ import annotations

import pytest

from ark import proactive_attention_preview as attention


@pytest.mark.parametrize("carrier", ("AttentionBudgetPolicy", "SyntheticSurfaceMarker"))
def test_input_constructor_identity_rejects_hostile_equality_without_running_it(
    monkeypatch: pytest.MonkeyPatch, carrier: str,
) -> None:
    policy = attention.AttentionBudgetPolicy("a" * 64, "b" * 64, 1, 100, 2, False)
    marker = attention.SyntheticSurfaceMarker(
        "a" * 64, "b" * 64, "c" * 64, "d" * 64, 20,
    )
    calls: list[str] = []

    class HostileConstructor:
        def __call__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("call")
            raise AssertionError("replaced constructor must not run")

        def __eq__(self, _other: object) -> bool:
            calls.append("eq")
            raise AssertionError("replaced constructor equality must not run")

        def __ne__(self, _other: object) -> bool:
            calls.append("ne")
            raise AssertionError("replaced constructor inequality must not run")

    with monkeypatch.context() as patch:
        patch.setattr(getattr(attention, carrier), "__init__", HostileConstructor())
        with pytest.raises(
            attention.AttentionPreviewRejected,
            match="authority definition changed",
        ):
            attention.preview_proactive_attention(
                policy, (marker,),
                occurrence_sha256="e" * 64,
                observation_sha256="f" * 64,
                observed_now_ms=50,
            )
    assert calls == []


def test_original_input_constructors_keep_review_only_without_notification() -> None:
    policy = attention.AttentionBudgetPolicy("a" * 64, "b" * 64, 1, 100, 2, False)
    preview = attention.preview_proactive_attention(
        policy, (), occurrence_sha256="c" * 64,
        observation_sha256="d" * 64, observed_now_ms=50,
    )
    assert preview.disposition == "REVIEW_ONLY"
    assert preview.notification_authorized is False
    assert preview.action_authorized is False
    assert preview.trusted_clock_verified is False
    assert preview.consent_verified is False
