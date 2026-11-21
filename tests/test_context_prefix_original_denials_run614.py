"""Offline Context prefix reviews never run counterfeit denial callbacks.

Synthetic SQLite fixtures only. No consent, disclosure, or dispatch authority.
"""

from __future__ import annotations

import pytest
from test_personal_context_retained_replay_prefix_run511 import _first

from ark import personal_context_replay_prefix_review as prefix


@pytest.mark.parametrize("field", prefix._DENIAL_NAMES)
def test_false_looking_authority_getter_rejected_without_execution(
    tmp_path, monkeypatch: pytest.MonkeyPatch, field: str,
) -> None:
    ledger, retained = _first(tmp_path)
    calls = []

    def forged(_self):
        calls.append(field)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(prefix.OfflineContextPrefixReview, field, property(forged))
        with pytest.raises(prefix.OfflineContextPrefixRejected, match="authority"):
            prefix.review_retained_context_replay_prefix(ledger, retained)
    assert calls == []


def test_forged_result_constructor_rejected_before_call(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger, retained = _first(tmp_path)
    calls = []

    def forged(*_args, **_kwargs):
        calls.append("constructor")
        return object()

    with monkeypatch.context() as patch:
        patch.setattr(prefix, "OfflineContextPrefixReview", forged)
        with pytest.raises(prefix.OfflineContextPrefixRejected, match="authority"):
            prefix.review_retained_context_replay_prefix(ledger, retained)
    assert calls == []


def test_descriptor_injected_while_hashing_cannot_run(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger, retained = _first(tmp_path)
    calls = []
    original = prefix.json.dumps

    def forged(_self):
        calls.append("denial getter")
        return False

    def change_during_hashing(*args, **kwargs):
        monkeypatch.setattr(
            prefix.OfflineContextPrefixReview,
            "consent_verified",
            property(forged),
        )
        return original(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(prefix.json, "dumps", change_during_hashing)
        with pytest.raises(
            prefix.OfflineContextPrefixRejected, match="digest implementation changed",
        ):
            prefix.review_retained_context_replay_prefix(ledger, retained)
    assert calls == []


def test_unmodified_review_still_denies_every_authority(tmp_path) -> None:
    ledger, retained = _first(tmp_path)
    result = prefix.review_retained_context_replay_prefix(ledger, retained)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.retained_count == result.current_count == 1
    for name in prefix._DENIAL_NAMES:
        assert getattr(result, name) is False
