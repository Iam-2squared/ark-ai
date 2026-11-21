"""Retained attention preview must not drift after its source callbacks."""

import pytest

from ark import attention_retained_prefix_review as prefix
from ark import proactive_attention_preview as attention


def policy():
    return attention.AttentionBudgetPolicy("a" * 64, "b" * 64, 10, 100, 4, False)


def marker():
    return attention.SyntheticSurfaceMarker(
        "a" * 64, "b" * 64, "1" * 64, "2" * 64, 20,
    )


def unchanged_prior_digest():
    return attention.preview_proactive_attention(
        policy(), (), occurrence_sha256="0" * 64,
        observation_sha256="0" * 64, observed_now_ms=10,
    ).history_sha256


@pytest.mark.parametrize("which", (0, 1))
@pytest.mark.parametrize(
    "field", ("disposition", "next_review_at_ms",
              "surfaced_count_in_window", "history_sha256", "review_sha256"),
)
def test_preview_scalar_mutated_during_prefix_hash_rejected(
    monkeypatch, which, field,
):
    retained_digest = unchanged_prior_digest()
    # Observe legitimate constructor results without replacing __init__.
    # The stronger output-lookup preflight now vetoes even a passive hook.
    # No preview is constructed, and the later JSON mutation is unreachable.
    original_getattribute = attention.AttentionBudgetPreview.__getattribute__
    captured = []

    def capture(self, name):
        if name == "notification_authorized" and not any(
            item is self for item in captured
        ):
            captured.append(self)
        return original_getattribute(self, name)

    monkeypatch.setattr(
        attention.AttentionBudgetPreview, "__getattribute__", capture,
    )
    original_json = prefix.json.dumps
    calls = []
    touched = []

    def mutate(*args, **kwargs):
        calls.append(True)
        # Each original preview uses two JSON serializations; the fifth is
        # the prefix evidence serialization after both delegates returned.
        if len(calls) == 5:
            report = captured[which]
            original_value = getattr(report, field)
            if field.endswith("_sha256"):
                changed = "f" * 64
            elif field == "next_review_at_ms":
                changed = 90
            elif field == "disposition":
                changed = "FORGED"
            else:
                changed = original_value + 1
            object.__setattr__(report, field, changed)
            touched.append(field)
        return original_json(*args, **kwargs)

    monkeypatch.setattr(prefix.json, "dumps", mutate)
    with pytest.raises(prefix.AttentionPrefixRejected, match="attention source preview rejected"):
        prefix.review_attention_retained_prefix(
            policy(), (), (marker(),),
            retained_history_sha256=retained_digest,
            retained_now_ms=10, observed_now_ms=30,
        )
    assert touched == []
    assert captured == []
    assert calls == []


def test_unchanged_preview_evidence_remains_no_authority():
    digest = unchanged_prior_digest()
    result = prefix.review_attention_retained_prefix(
        policy(), (), (marker(),), retained_history_sha256=digest,
        retained_now_ms=10, observed_now_ms=30,
    )
    assert result.classification == "APPEND_ONLY"
    assert result.appended_count == 1
    assert result.notification_authorized is False
    assert result.append_authorized is False
    assert result.automatic_replay_authorized is False
