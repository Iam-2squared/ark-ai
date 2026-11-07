"""Privacy veto reviews must not invoke substituted deny-only getters.

All tests use a disposable local fixture ledger. Missing veto is never consent.
"""

from __future__ import annotations

import pytest

import ark.disconnected_privacy_veto as veto

_OWNER = "a" * 64
_SCOPE = "b" * 64
_DENIALS = (
    "consent_verified",
    "context_release_authorized",
    "user_identity_authenticated",
)


def _case(tmp_path):
    ledger = veto.DisconnectedPrivacyVetoLedger(tmp_path / "veto.sqlite3")
    return ledger, ledger.witness()


def _review(ledger, retained):
    return ledger.review(
        owner_sha256=_OWNER, scope_sha256=_SCOPE, retained=retained,
    )


@pytest.mark.parametrize("flag", _DENIALS)
@pytest.mark.parametrize("stage", ("preinstalled", "second_inspect"))
def test_false_looking_counterfeit_rejected_without_getter(
    tmp_path, monkeypatch, flag, stage,
):
    ledger, retained = _case(tmp_path)
    getter_calls = []

    class Counterfeit:
        def __get__(self, _instance, _owner=None):
            getter_calls.append(flag)
            return False

    forged = Counterfeit()
    if stage == "preinstalled":
        opened = []

        def forbidden_open(*args, **kwargs):
            opened.append(True)
            raise AssertionError("counterfeit must be rejected before SQLite")

        monkeypatch.setattr(ledger, "_open", forbidden_open)
        monkeypatch.setattr(veto.OfflinePrivacyVetoReview, flag, forged)
    else:
        original_inspect = veto._inspect
        seen = []

        def swap_after_second_inspect(conn):
            result = original_inspect(conn)
            seen.append(True)
            if len(seen) == 2:
                monkeypatch.setattr(veto.OfflinePrivacyVetoReview, flag, forged)
            return result

        monkeypatch.setattr(veto, "_inspect", swap_after_second_inspect)

    with pytest.raises(
        veto.OfflinePrivacyVetoRejected, match="review acquired authority",
    ):
        _review(ledger, retained)
    assert getter_calls == []
    if stage == "preinstalled":
        assert opened == []
    else:
        assert len(seen) == 2


def test_fake_review_class_copying_original_properties_cannot_construct(
    tmp_path, monkeypatch,
):
    ledger, retained = _case(tmp_path)
    original = veto.OfflinePrivacyVetoReview
    calls = []

    def construct(self, *args):
        calls.append(args)

    namespace = {name: vars(original)[name] for name in _DENIALS}
    namespace["__init__"] = construct
    monkeypatch.setattr(
        veto, "OfflinePrivacyVetoReview",
        type("CounterfeitPrivacyReview", (), namespace),
    )
    with pytest.raises(
        veto.OfflinePrivacyVetoRejected, match="review acquired authority",
    ):
        _review(ledger, retained)
    assert calls == []


def test_original_readonly_veto_stays_non_authorizing(tmp_path):
    ledger, retained = _case(tmp_path)
    review = _review(ledger, retained)
    assert review.local_veto_seen is False
    assert all(getattr(review, name) is False for name in _DENIALS)
