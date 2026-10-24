"""Registry-bound mock approval claims never confer consent or Tool authority."""

import hashlib

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_claim_review import (
    SyntheticApprovalRejected,
    make_synthetic_approval_claim,
    review_synthetic_approval_claim,
)


class NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("synthetic approval review must not dispatch")


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _base(*, effect=Effect.WRITE, backend="mock"):
    call = ToolCall("writer", "write", "local", {"data": "test-only"})
    registry = ToolRegistry((
        ToolRegistration("writer", "write", effect, backend, NeverExecute()),
    ))
    return registry, call


def _fields(**changes):
    values = {
        "issuer_digest": _digest("issuer"),
        "subject_digest": _digest("subject"),
        "purpose_digest": _digest("purpose"),
        "recipient_digest": _digest("recipient"),
        "nonce_digest": _digest("nonce"),
        "issued_at_ms": 10,
        "expires_at_ms": 100,
    }
    values.update(changes)
    return values


def _claim(registry, call, **changes):
    return make_synthetic_approval_claim(registry, call, **_fields(**changes))


def _review(claim, registry, call, **changes):
    values = {
        "issuer_digest": claim.issuer_digest,
        "subject_digest": claim.subject_digest,
        "purpose_digest": claim.purpose_digest,
        "recipient_digest": claim.recipient_digest,
        "now_ms": 20,
        "cancelled_ids": frozenset(),
    }
    values.update(changes)
    return review_synthetic_approval_claim(claim, registry, call, **values)


def test_valid_local_claim_is_content_minimized_and_never_authorizes():
    registry, call = _base()
    claim = _claim(registry, call)
    assert claim.approval_id.startswith("approval_")
    assert claim.bound_action_id.startswith("bound_")
    # Field labels are intentionally human-readable; values are only digests.
    assert claim.issuer_digest == _digest("issuer")
    assert claim.subject_digest == _digest("subject")
    assert claim.purpose_digest == _digest("purpose")
    assert claim.recipient_digest == _digest("recipient")
    assert "test-only" not in repr(claim)
    result = _review(claim, registry, call)
    assert result.approval_id == claim.approval_id
    assert result.dispatch_authorized is False
    assert result.human_consent_verified is False
    assert result.automatic_replay_authorized is False
    assert claim.dispatch_authorized is False
    assert claim.human_consent_verified is False
    assert claim.automatic_replay_authorized is False


@pytest.mark.parametrize(
    "change",
    [
        {"issuer_digest": _digest("other-issuer")},
        {"subject_digest": _digest("other-subject")},
        {"purpose_digest": _digest("other-purpose")},
        {"recipient_digest": _digest("other-recipient")},
        {"nonce_digest": _digest("other-nonce")},
        {"expires_at_ms": 101},
    ],
)
def test_every_claim_dimension_changes_identity(change):
    registry, call = _base()
    first = _claim(registry, call)
    second = _claim(registry, call, **change)
    assert first.approval_id != second.approval_id
    assert _claim(registry, call, **change) == second


@pytest.mark.parametrize(
    "review_field",
    ["issuer_digest", "subject_digest", "purpose_digest", "recipient_digest"],
)
def test_actor_purpose_and_recipient_mismatch_are_denied(review_field):
    registry, call = _base()
    claim = _claim(registry, call)
    with pytest.raises(SyntheticApprovalRejected, match="differs"):
        _review(claim, registry, call, **{review_field: _digest("not-same")})


def test_different_registry_backend_cannot_rebind_a_claim():
    registry, call = _base()
    claim = _claim(registry, call)
    different, _call = _base(backend="another-backend")
    with pytest.raises(SyntheticApprovalRejected, match="binding differs"):
        _review(claim, different, call)


def test_cancelled_claim_is_rejected_before_coherence_receipt():
    registry, call = _base()
    claim = _claim(registry, call)
    with pytest.raises(SyntheticApprovalRejected, match="cancelled"):
        _review(claim, registry, call, cancelled_ids=frozenset({claim.approval_id}))


@pytest.mark.parametrize("now_ms", [-1, 9, 100, 101, 2**63, True])
def test_expired_early_or_invalid_caller_clock_is_rejected(now_ms):
    registry, call = _base()
    claim = _claim(registry, call)
    with pytest.raises(SyntheticApprovalRejected):
        _review(claim, registry, call, now_ms=now_ms)


def test_exact_expiry_boundary_uses_open_upper_bound():
    registry, call = _base()
    claim = _claim(registry, call)
    assert _review(claim, registry, call, now_ms=10).observed_at_ms == 10
    assert _review(claim, registry, call, now_ms=99).observed_at_ms == 99


@pytest.mark.parametrize(
    "change",
    [
        {"issuer_digest": "missing-prefix"},
        {"nonce_digest": "f" * 63},
        {"issued_at_ms": True},
        {"expires_at_ms": 10},
        {"issued_at_ms": -1},
        {"expires_at_ms": 2**63},
    ],
)
def test_invalid_claim_inputs_rejected(change):
    registry, call = _base()
    with pytest.raises(SyntheticApprovalRejected):
        _claim(registry, call, **change)


def test_no_read_effect_claim_even_when_scope_and_capability_match():
    registry, call = _base(effect=Effect.READ)
    with pytest.raises(SyntheticApprovalRejected, match="only WRITE"):
        _claim(registry, call)


@pytest.mark.parametrize("field", ["approval_id", "recipient_digest", "expires_at_ms"])
def test_reflectively_altered_claim_fails_closed(field):
    registry, call = _base()
    claim = _claim(registry, call)
    replacement = 101 if field == "expires_at_ms" else (
        "approval_" + "f" * 64 if field == "approval_id" else _digest("forged")
    )
    object.__setattr__(claim, field, replacement)
    with pytest.raises(SyntheticApprovalRejected, match="modified"):
        _review(claim, registry, call)


@pytest.mark.parametrize("bad", [set(), ("approval_" + "1" * 64,), frozenset({"bad"}), 0])
def test_cancellation_source_must_be_explicit_exact_frozenset(bad):
    registry, call = _base()
    claim = _claim(registry, call)
    with pytest.raises(SyntheticApprovalRejected, match="exact"):
        _review(claim, registry, call, cancelled_ids=bad)


def test_wrong_type_for_registry_and_call_is_refused():
    registry, call = _base()
    claim = _claim(registry, call)
    with pytest.raises(SyntheticApprovalRejected, match="exact"):
        _review(claim, "registry", call)
    with pytest.raises(SyntheticApprovalRejected, match="exact"):
        _review(claim, registry, "call")
