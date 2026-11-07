"""Attention receipt output hooks must remain original and non-authorizing.

The synthetic preview never sends notifications. Allocation-hook poisoning
is confined to child interpreters to avoid contaminating unrelated tests.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from ark import proactive_attention_preview as attention

SHA = "a" * 64
TRIGGER = "b" * 64
CANDIDATE = "c" * 64


def _review():
    return attention.preview_proactive_attention(
        attention.AttentionBudgetPolicy(SHA, TRIGGER, 10, 100, 2, True),
        (),
        occurrence_sha256=CANDIDATE,
        observation_sha256=CANDIDATE,
        observed_now_ms=100,
    )


@pytest.mark.parametrize("name", attention._RESULT_FIELDS)
def test_preinstalled_output_slot_cannot_run_before_authority_denial(
    monkeypatch, name,
):
    def forbidden(_self):
        pytest.fail("untrusted output slot executed before preflight")

    monkeypatch.setattr(
        attention.AttentionBudgetPreview, name, property(forbidden),
    )
    with pytest.raises(
        attention.AttentionPreviewRejected, match="result changed",
    ):
        _review()


@pytest.mark.parametrize("hook", ("__new__", "__getattribute__", "__getattr__"))
def test_output_allocation_and_lookup_hooks_are_blocked_in_child_process(hook):
    source = """
from ark import proactive_attention_preview as attention

def forbidden(*args, **kwargs):
    raise AssertionError("untrusted receipt hook executed")

setattr(attention.AttentionBudgetPreview, HOOK, forbidden)
try:
    attention.preview_proactive_attention(
        attention.AttentionBudgetPolicy("a" * 64, "b" * 64, 10, 100, 2, True),
        (), occurrence_sha256="c" * 64, observation_sha256="c" * 64,
        observed_now_ms=100,
    )
except attention.AttentionPreviewRejected as exc:
    assert "result changed" in str(exc), str(exc)
else:
    raise AssertionError("injected output hook was accepted")
""".replace("HOOK", repr(hook))
    child = subprocess.run(
        [sys.executable, "-c", source],
        check=False, capture_output=True, text=True,
    )
    assert child.returncode == 0, child.stdout + child.stderr


def test_original_output_is_deterministic_and_denies_all_authority():
    first = _review()
    assert first == _review()
    assert first.disposition == "REVIEW_ONLY"
    assert first.notification_authorized is False
    assert first.action_authorized is False
    assert first.trusted_clock_verified is False
    assert first.consent_verified is False
