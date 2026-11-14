"""Synthetic attention inputs must not run rebound field lookup hooks.

The preview has no notification, trusted time, consent, or real action powers.
"""

import pytest

from ark import proactive_attention_preview as attention


def _inputs():
    policy = attention.AttentionBudgetPolicy(
        "a" * 64, "b" * 64, 1, 100, 1, False,
    )
    marker = attention.SyntheticSurfaceMarker(
        "a" * 64, "b" * 64, "c" * 64, "d" * 64, 90,
    )
    return policy, (marker,)


def _preview(policy, history):
    return attention.preview_proactive_attention(
        policy, history, occurrence_sha256="e" * 64,
        observation_sha256="f" * 64, observed_now_ms=100,
    )


@pytest.mark.parametrize("target", ("policy", "marker"))
@pytest.mark.parametrize("epoch", ("preinstalled", "digest_callback"))
def test_rebound_input_getattribute_is_not_invoked(
    monkeypatch, target, epoch,
):
    policy, history = _inputs()
    inspected = []
    kind = (
        attention.AttentionBudgetPolicy if target == "policy"
        else attention.SyntheticSurfaceMarker
    )

    def counterfeit_lookup(self, name):
        inspected.append(name)
        raise AssertionError("untrusted synthetic input getter executed")

    if epoch == "preinstalled":
        monkeypatch.setattr(kind, "__getattribute__", counterfeit_lookup)
    else:
        original_hash = attention.hashlib.sha256

        def inject_during_hash(payload=b""):
            if payload.startswith(attention._DOMAIN):
                monkeypatch.setattr(
                    kind, "__getattribute__", counterfeit_lookup,
                )
            return original_hash(payload)

        monkeypatch.setattr(attention.hashlib, "sha256", inject_during_hash)

    with pytest.raises(
        attention.AttentionPreviewRejected,
        match="attention authority definition changed",
    ):
        _preview(policy, history)
    assert inspected == []


@pytest.mark.parametrize("target", ("policy", "marker"))
def test_rebound_input_getattr_is_not_invoked(monkeypatch, target):
    policy, history = _inputs()
    inspected = []
    kind = (
        attention.AttentionBudgetPolicy if target == "policy"
        else attention.SyntheticSurfaceMarker
    )

    def injected_fallback(self, name):
        inspected.append(name)
        raise AssertionError("untrusted fallback invoked")

    monkeypatch.setattr(kind, "__getattr__", injected_fallback, raising=False)
    with pytest.raises(
        attention.AttentionPreviewRejected,
        match="attention authority definition changed",
    ):
        _preview(policy, history)
    assert inspected == []


def test_clean_synthetic_inputs_remain_non_authorizing():
    policy, history = _inputs()
    result = _preview(policy, history)
    assert result.disposition == "WINDOW_BUDGET_HOLD"
    assert result.notification_authorized is False
    assert result.action_authorized is False
    assert result.consent_verified is False
    assert result.trusted_clock_verified is False
