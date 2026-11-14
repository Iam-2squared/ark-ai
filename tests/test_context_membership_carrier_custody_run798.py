"""Privacy metadata admission pins carrier descriptors before reading fixtures."""

from __future__ import annotations

import pytest

from ark import offline_context_membership_guard as guard

_OWNER = "a" * 64
_SCOPE = "b" * 64
_RECORD = "ctx_" + "1" * 16


def _fixtures():
    record = guard.ContextRecordClaim(
        _RECORD, _OWNER, _SCOPE, "c" * 64, 10, 200,
    )
    veto = guard.ContextScopeVetoClaim(_SCOPE, False, 50, "d" * 64)
    return record, veto


def _review(record, veto):
    return guard.review_offline_context_membership(
        (record,), expected_record_ids=(_RECORD,),
        owner_digest=_OWNER, allowed_scope_digests=(_SCOPE,),
        scope_vetoes=(veto,), observed_at_ms=100, max_claim_age_ms=100,
    )


@pytest.mark.parametrize("carrier,field", (
    ("record", "record_id"),
    ("record", "owner_digest"),
    ("record", "scope_digest"),
    ("record", "content_sha256"),
    ("record", "captured_at_ms"),
    ("record", "expires_at_ms"),
    ("veto", "scope_digest"),
    ("veto", "revoked"),
    ("veto", "observed_at_ms"),
    ("veto", "continuity_sha256"),
))
def test_swapped_metadata_slot_denied_before_first_getter(monkeypatch, carrier, field):
    record, veto = _fixtures()
    seen = []

    def unexpected(self):
        seen.append(field)
        return "counterfeit"

    cls = guard.ContextRecordClaim if carrier == "record" else guard.ContextScopeVetoClaim
    with monkeypatch.context() as patch:
        patch.setattr(cls, field, property(unexpected))
        with pytest.raises(
            guard.OfflineContextAdmissionRejected, match="original Context authority",
        ):
            _review(record, veto)
    assert seen == []


@pytest.mark.parametrize("carrier", ("record", "veto", "result"))
def test_swapped_attribute_lookup_denied_pre_metadata(monkeypatch, carrier):
    record, veto = _fixtures()
    seen = []
    cls = {
        "record": guard.ContextRecordClaim,
        "veto": guard.ContextScopeVetoClaim,
        "result": guard.OfflineContextMembershipReview,
    }[carrier]

    def unexpected(self, name):
        seen.append(name)
        return object.__getattribute__(self, name)

    with monkeypatch.context() as patch:
        patch.setattr(cls, "__getattribute__", unexpected)
        with pytest.raises(
            guard.OfflineContextAdmissionRejected, match="original Context authority",
        ):
            _review(record, veto)
    assert seen == []


@pytest.mark.parametrize("carrier", ("record", "veto", "result"))
def test_swapped_constructor_denied_before_call(monkeypatch, carrier):
    record, veto = _fixtures()
    called = []
    cls = {
        "record": guard.ContextRecordClaim,
        "veto": guard.ContextScopeVetoClaim,
        "result": guard.OfflineContextMembershipReview,
    }[carrier]

    def unexpected(self, *args, **kwargs):
        called.append((args, kwargs))

    with monkeypatch.context() as patch:
        patch.setattr(cls, "__init__", unexpected)
        with pytest.raises(
            guard.OfflineContextAdmissionRejected, match="original Context authority",
        ):
            _review(record, veto)
    assert not called


@pytest.mark.parametrize("field", (
    "owner_digest", "record_count", "scope_count", "membership_sha256",
))
def test_swapped_review_field_denied_before_constructor(monkeypatch, field):
    record, veto = _fixtures()
    with monkeypatch.context() as patch:
        patch.setattr(
            guard.OfflineContextMembershipReview, field, property(lambda _: "fake"),
        )
        with pytest.raises(
            guard.OfflineContextAdmissionRejected, match="original Context authority",
        ):
            _review(record, veto)


def test_original_membership_digest_still_inert_and_deterministic():
    first = _review(*_fixtures())
    second = _review(*_fixtures())
    assert first == second
    assert first.record_count == first.scope_count == 1
    assert first.consent_verified is False
    assert first.disclosure_authorized is False
    assert first.retention_authorized is False
    assert first.trusted_clock_verified is False
