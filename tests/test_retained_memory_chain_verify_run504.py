"""Independent Memory chain receipt verification: local evidence never grants access."""

from dataclasses import replace

import pytest

import ark.memory.retained_epoch_chain as mod
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview
from ark.memory.contracts import MemorySchemaError


def epochs():
    scope = ("a" * 64,)
    return (
        AtomicMemoryEpochReview(scope, (1,), (1,), (1,), "b" * 64, "c" * 64),
        AtomicMemoryEpochReview(scope, (1,), (2,), (2,), "d" * 64, "e" * 64),
        AtomicMemoryEpochReview(scope, (1,), (3,), (3,), "f" * 64, "1" * 64),
    )


def test_valid_retained_chain_receipt_recomputes_without_grant():
    source = epochs()
    receipt = mod.review_retained_memory_chain(source)
    assert receipt.added_event_counts == (2,)
    assert mod.verify_retained_memory_chain(receipt, source) is None
    assert receipt.memory_disclosure_authorized is False


@pytest.mark.parametrize("field,value", [
    ("observations", 2),
    ("observations", True),
    ("scope_fingerprints", ("f" * 64,)),
    ("scope_fingerprints", ["a" * 64]),
    ("added_event_counts", (1,)),
    ("added_event_counts", (True,)),
    ("status", "UNCHANGED_LOCAL_CONTENT"),
    ("chain_digest", "f" * 64),
    ("chain_digest", 123),
])
def test_independent_receipt_field_mutations_rejected(field, value):
    source = epochs()
    original = mod.review_retained_memory_chain(source)
    with pytest.raises(MemorySchemaError, match="integrity"):
        mod.verify_retained_memory_chain(
            replace(original, **{field: value}), source,
        )


def test_spoofed_dataclass_equality_never_bypasses_digest(monkeypatch):
    source = epochs()
    forged = replace(mod.review_retained_memory_chain(source), chain_digest="f" * 64)
    monkeypatch.setattr(mod.RetainedMemoryChainReview, "__eq__", lambda self, other: True)
    with pytest.raises(MemorySchemaError, match="integrity"):
        mod.verify_retained_memory_chain(forged, source)


@pytest.mark.parametrize("mutation", ["receipt", "input"])
def test_denial_callback_mutations_cannot_escape_final_integrity_check(
    monkeypatch, mutation,
):
    source = epochs()
    receipt = mod.review_retained_memory_chain(source)

    def malicious(self):
        if self is receipt:
            if mutation == "receipt":
                object.__setattr__(self, "chain_digest", "f" * 64)
            else:
                object.__setattr__(source[-1], "content_digest", "f" * 64)
        return False

    monkeypatch.setattr(
        mod.RetainedMemoryChainReview, "dispatch_authorized",
        property(malicious),
    )
    with pytest.raises(MemorySchemaError, match="changed"):
        mod.verify_retained_memory_chain(receipt, source)


def test_receipt_subclass_rejected():
    source = epochs()
    receipt = mod.review_retained_memory_chain(source)

    class Subclass(mod.RetainedMemoryChainReview):
        pass

    with pytest.raises(MemorySchemaError, match="exact"):
        mod.verify_retained_memory_chain(
            Subclass(
                receipt.observations, receipt.scope_fingerprints,
                receipt.added_event_counts, receipt.status, receipt.chain_digest,
            ),
            source,
        )
