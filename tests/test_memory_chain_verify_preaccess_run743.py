"""Detached retained Memory chain callback custody; no action or read grant."""

from __future__ import annotations

import re

import pytest

import ark.memory.retained_epoch_chain as chain
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview
from ark.memory.contracts import MemorySchemaError


def _epochs() -> tuple[AtomicMemoryEpochReview, ...]:
    scope = ("a" * 64,)
    return (
        AtomicMemoryEpochReview(scope, (1,), (1,), (1,), "b" * 64, "c" * 64),
        AtomicMemoryEpochReview(scope, (1,), (2,), (2,), "d" * 64, "e" * 64),
    )


def test_unmodified_detached_verifier_still_denies_authority():
    epochs = _epochs()
    receipt = chain.review_retained_memory_chain(epochs)
    assert chain.verify_retained_memory_chain(receipt, epochs) is None
    assert receipt.historical_prefix_proven is False
    assert receipt.memory_disclosure_authorized is False
    assert receipt.dispatch_authorized is False


@pytest.mark.parametrize("target,replacement", (
    ("review_retained_memory_chain", lambda *_: None),
    ("review_retained_memory_epoch", lambda *_: None),
    ("_validate_epoch", lambda *_: None),
    ("_SHA", re.compile(".*")),
    ("_MAX_EPOCHS", 1000000),
    ("_RESULT_TYPE", object),
    ("json_module", object()),
    ("hashlib_module", object()),
    ("json_dumps", lambda *_args, **_kwargs: "{}"),
    ("sha256", lambda *_args: None),
))
def test_substituted_callback_or_budget_rejected_before_private_epoch_access(
    monkeypatch, target, replacement,
):
    epochs = _epochs()
    receipt = chain.review_retained_memory_chain(epochs)
    # Construct the receipt before replacing any helper so that the verifier
    # must reject on ingress rather than a malformed comparison result.
    if target == "json_module":
        monkeypatch.setattr(chain, "json", replacement)
    elif target == "hashlib_module":
        monkeypatch.setattr(chain, "hashlib", replacement)
    elif target == "json_dumps":
        monkeypatch.setattr(chain.json, "dumps", replacement)
    elif target == "sha256":
        monkeypatch.setattr(chain.hashlib, "sha256", replacement)
    else:
        monkeypatch.setattr(chain, target, replacement)
    with pytest.raises(MemorySchemaError, match="protocol"):
        chain.verify_retained_memory_chain(receipt, epochs)


@pytest.mark.parametrize("field", (
    "chain_digest", "status", "scope_fingerprints", "added_event_counts",
))
def test_equal_value_receipt_replacement_during_last_denial_is_detected(
    monkeypatch, field,
):
    epochs = _epochs()
    receipt = chain.review_retained_memory_chain(epochs)
    called = False

    def reflected_denial(self):
        nonlocal called
        if self is receipt:
            called = True
            original = getattr(self, field)
            if type(original) is str:
                replaced = ("!" + original)[1:]
            else:
                replaced = tuple(list(original))
            assert replaced == original
            assert replaced is not original
            object.__setattr__(self, field, replaced)
        return False

    monkeypatch.setattr(
        chain.RetainedMemoryChainReview, "dispatch_authorized",
        property(reflected_denial),
    )
    with pytest.raises(MemorySchemaError, match="changed"):
        chain.verify_retained_memory_chain(receipt, epochs)
    assert called
