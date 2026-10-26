"""Exact synthetic Context membership and stale/veto rejection cases."""

from dataclasses import FrozenInstanceError

import pytest

from ark.offline_context_membership_guard import (
    ContextRecordClaim,
    ContextScopeVetoClaim,
    OfflineContextAdmissionRejected,
    OfflineContextMembershipReview,
    review_offline_context_membership,
)

OWNER = "a" * 64
SCOPE = "b" * 64
SECOND = "c" * 64
CONTENT = "d" * 64
CONTINUITY = "e" * 64
ONE = "ctx_" + "1" * 16
TWO = "ctx_" + "2" * 16
NOW = 1000


def record(id=ONE, owner=OWNER, scope=SCOPE, content=CONTENT, captured=900, expires=2000):
    return ContextRecordClaim(id, owner, scope, content, captured, expires)


def veto(scope=SCOPE, revoked=False, observed=995, continuity=CONTINUITY):
    return ContextScopeVetoClaim(scope, revoked, observed, continuity)


def review(rows=None, *, expected=(ONE,), owner=OWNER, scopes=(SCOPE,),
           vetoes=None, at=NOW, age=100):
    return review_offline_context_membership(
        (record(),) if rows is None else rows, expected_record_ids=expected,
        owner_digest=owner, allowed_scope_digests=scopes,
        scope_vetoes=(veto(),) if vetoes is None else vetoes,
        observed_at_ms=at, max_claim_age_ms=age,
    )


def test_success_is_never_permission_and_emits_no_plaintext():
    result = review()
    assert type(result) is OfflineContextMembershipReview
    assert result.record_count == result.scope_count == 1
    assert result.owner_digest == OWNER
    assert len(result.membership_sha256) == 64
    assert not result.consent_verified
    assert not result.disclosure_authorized
    assert not result.retention_authorized
    assert not result.trusted_clock_verified
    assert not hasattr(result, "content")
    with pytest.raises(FrozenInstanceError):
        result.record_count = 2


def test_multiple_scopes_and_expected_membership():
    left = review((record(), record(TWO, scope=SECOND)), expected=(ONE, TWO),
                  scopes=(SCOPE, SECOND), vetoes=(veto(), veto(SECOND)))
    right = review((record(), record(TWO, scope=SECOND)), expected=(ONE, TWO),
                   scopes=(SCOPE, SECOND), vetoes=(veto(), veto(SECOND)))
    assert left == right
    assert left.membership_sha256 != review().membership_sha256


def test_exact_expiry_boundary_and_age_boundary():
    review((record(captured=900, expires=1001),))
    with pytest.raises(OfflineContextAdmissionRejected):
        review((record(expires=1000),))
    with pytest.raises(OfflineContextAdmissionRejected):
        review((record(captured=899),))
    with pytest.raises(OfflineContextAdmissionRejected):
        review(vetoes=(veto(observed=899),))


@pytest.mark.parametrize("bad", [None, True, "a", "A" * 64, "a" * 63])
def test_invalid_owner_rejected(bad):
    with pytest.raises(OfflineContextAdmissionRejected):
        review(owner=bad)


@pytest.mark.parametrize("claims,expected", [
    ((), ()),
    ((record(),), ()),
    ((record(),), (TWO,)),
    ((record(), record()), (ONE, TWO)),
    ((record(TWO), record()), (ONE, TWO)),
    ((record(), record(TWO)), (TWO, ONE)),
    ((record(),), [ONE]),
    ((record(),), (ONE, ONE)),
    ((record(),), ("ctx_bad",)),
])
def test_record_membership_denials(claims, expected):
    with pytest.raises(OfflineContextAdmissionRejected):
        review(claims, expected=expected)


@pytest.mark.parametrize("row", [
    record(owner="f" * 64), record(scope=SECOND), record(content="X" * 64),
    record(captured=-1), record(captured=1001), record(captured=True),
    record(expires=True), record(expires=1000), record(expires=2**63),
    record(captured=899), record(expires=-1), record(id="ctx_bad"),
])
def test_record_integrity_denials(row):
    with pytest.raises(OfflineContextAdmissionRejected):
        review((row,))


@pytest.mark.parametrize("vetoes", [
    (), (veto(revoked=True),), (veto(revoked=1),),
    (veto(scope=SECOND),), (veto(observed=1001),),
    (veto(observed=899),), (veto(continuity="BAD"),),
    (veto(observed=True),),
])
def test_veto_denials(vetoes):
    with pytest.raises(OfflineContextAdmissionRejected):
        review(vetoes=vetoes)


@pytest.mark.parametrize("kwargs", [
    {"at": True}, {"at": -1}, {"at": 2**63},
    {"age": True}, {"age": -1}, {"age": 2**63},
    {"scopes": []}, {"scopes": ()}, {"scopes": (SCOPE, SCOPE)},
    {"scopes": (SECOND, SCOPE)}, {"scopes": ("a",)},
])
def test_envelope_denials(kwargs):
    with pytest.raises(OfflineContextAdmissionRejected):
        review(**kwargs)


def test_exact_type_rejected():
    class Child(ContextRecordClaim):
        pass
    with pytest.raises(OfflineContextAdmissionRejected):
        review((Child(ONE, OWNER, SCOPE, CONTENT, 900, 2000),))
    class VetoChild(ContextScopeVetoClaim):
        pass
    with pytest.raises(OfflineContextAdmissionRejected):
        review(vetoes=(VetoChild(SCOPE, False, 995, CONTINUITY),))
    with pytest.raises(OfflineContextAdmissionRejected):
        review_offline_context_membership(
            [record()], expected_record_ids=(ONE,), owner_digest=OWNER,
            allowed_scope_digests=(SCOPE,), scope_vetoes=(veto(),),
            observed_at_ms=NOW, max_claim_age_ms=100,
        )


def test_32_record_upper_bound():
    rows = tuple(record("ctx_" + f"{i:016x}") for i in range(32))
    result = review(rows, expected=tuple(row.record_id for row in rows))
    assert result.record_count == 32
    with pytest.raises(OfflineContextAdmissionRejected):
        review(rows + (record("ctx_" + "f" * 16),),
               expected=tuple(row.record_id for row in rows) + ("ctx_" + "f" * 16,))


def test_digest_changes_with_representative_metadata():
    base = review()
    assert base.membership_sha256 != review((record(content="0" * 64),)).membership_sha256
    assert base.membership_sha256 != review(vetoes=(veto(observed=996),)).membership_sha256
    assert base.membership_sha256 != review(at=999).membership_sha256


def test_reflective_record_replacement_during_hash(monkeypatch):
    from ark import offline_context_membership_guard as mod
    row = record()
    original = mod.hashlib.sha256
    def changed(payload):
        object.__setattr__(row, "content_sha256", CONTENT.encode().decode())
        return original(payload)
    monkeypatch.setattr(mod.hashlib, "sha256", changed)
    with pytest.raises(OfflineContextAdmissionRejected, match="carrier replaced"):
        review((row,))


def test_reflective_veto_replacement_during_hash(monkeypatch):
    from ark import offline_context_membership_guard as mod
    claim = veto()
    original = mod.hashlib.sha256
    def changed(payload):
        object.__setattr__(claim, "continuity_sha256", CONTINUITY.encode().decode())
        return original(payload)
    monkeypatch.setattr(mod.hashlib, "sha256", changed)
    with pytest.raises(OfflineContextAdmissionRejected, match="carrier replaced"):
        review(vetoes=(claim,))
