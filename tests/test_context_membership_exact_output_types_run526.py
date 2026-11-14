"""Exact type custody for disconnected privacy admission counts.

No live ContextStore, plaintext, consent, network, or ToolBackend is used.
"""

from __future__ import annotations

import pytest

import ark.offline_context_membership_guard as mod


def _admission():
    owner = "a" * 64
    scope = "b" * 64
    record_id = "ctx_" + "1" * 16
    return mod.review_offline_context_membership(
        (mod.ContextRecordClaim(record_id, owner, scope, "c" * 64, 10, 200),),
        expected_record_ids=(record_id,),
        owner_digest=owner,
        allowed_scope_digests=(scope,),
        scope_vetoes=(mod.ContextScopeVetoClaim(scope, False, 50, "d" * 64),),
        observed_at_ms=100,
        max_claim_age_ms=100,
    )


@pytest.mark.parametrize("field", ("record_count", "scope_count"))
@pytest.mark.parametrize("replacement", (True, 1.0))
def test_false_authority_callback_cannot_substitute_numeric_type(
    monkeypatch, field, replacement,
):
    def mutate(self):
        object.__setattr__(self, field, replacement)
        return False

    monkeypatch.setattr(
        mod.OfflineContextMembershipReview, "trusted_clock_verified",
        property(mutate),
    )
    with pytest.raises(mod.OfflineContextAdmissionRejected, match="original Context authority"):
        _admission()


@pytest.mark.parametrize("field", ("record_count", "scope_count"))
def test_constructor_must_not_return_bool_as_count(monkeypatch, field):
    original = mod.OfflineContextMembershipReview

    def forged_constructor(*args):
        result = original(*args)
        object.__setattr__(result, field, True)
        return result

    monkeypatch.setattr(mod, "OfflineContextMembershipReview", forged_constructor)
    with pytest.raises(mod.OfflineContextAdmissionRejected, match="original Context authority"):
        _admission()


def test_regular_synthetic_admission_remains_diagnostic():
    result = _admission()
    assert type(result.record_count) is int
    assert type(result.scope_count) is int
    assert result.record_count == result.scope_count == 1
    assert result.consent_verified is False
    assert result.disclosure_authorized is False
    assert result.retention_authorized is False
    assert result.trusted_clock_verified is False


@pytest.mark.parametrize("target_permission", [
    "consent_verified", "disclosure_authorized", "retention_authorized",
])
@pytest.mark.parametrize("replacement_value", [True, False])
def test_last_false_denial_cannot_replace_an_earlier_authority_descriptor(
    monkeypatch, target_permission, replacement_value,
):
    original = mod._MEMBERSHIP_RESULT_TYPE

    def change_previous_descriptor(self):
        monkeypatch.setattr(
            original, target_permission,
            property(lambda ignored: replacement_value),
        )
        return False

    monkeypatch.setattr(
        original, "trusted_clock_verified", property(change_previous_descriptor),
    )
    with pytest.raises(
        mod.OfflineContextAdmissionRejected, match="original Context authority",
    ):
        _admission()
