"""Offline observation lineage rejects fabricated parents and stale metadata."""

import hashlib
from pathlib import Path

import pytest

from ark.observation_lineage_review import (
    SyntheticObservationLineageRejected,
    review_synthetic_observation_lineage,
)
from ark.observations import ObservationEnvelope, ObservationKind


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _envelope(
    content: bytes,
    *,
    parent: str | None = None,
    source: str = "fixture",
    scope: str = "local:private",
    at: int = 100,
    adapter: str = "fixture:text",
):
    return ObservationEnvelope(
        ObservationKind.TEXT, source, adapter, scope,
        at, _digest(content), parent,
    )


def _review(envelopes, *, at=110, age=10):
    return review_synthetic_observation_lineage(
        envelopes, privacy_scope="local:private",
        now_ms=at, max_age_ms=age,
    )


def test_multi_adapter_parent_chain_is_inert(tmp_path: Path):
    root = _envelope(b"root", adapter="fixture:image")
    child = _envelope(
        b"child", parent=root.content_sha256,
        at=103, adapter="fixture:derived-text",
    )
    grandchild = _envelope(
        b"grandchild", parent=child.content_sha256, at=108,
    )
    witness = _review((root, child, grandchild))
    assert witness.observation_count == 3
    assert witness.lineage_digest.startswith("olineage_")
    assert witness.media_capture_authorized is False
    assert witness.disclosure_authorized is False
    assert witness.dispatch_authorized is False
    assert not hasattr(witness, "raw_media")
    assert not hasattr(witness, "content")


def test_input_order_does_not_change_canonical_lineage_digest():
    root = _envelope(b"root")
    child = _envelope(b"child", parent=root.content_sha256, at=103)
    first = _review((root, child))
    second = _review((child, root))
    assert first.lineage_digest == second.lineage_digest


def test_missing_parent_hash_cannot_be_assumed_trustworthy():
    child = _envelope(b"child", parent="f" * 64)
    with pytest.raises(SyntheticObservationLineageRejected, match="unresolved"):
        _review((child,))


def test_duplicate_content_parent_identity_is_ambiguous():
    first = _envelope(b"same", adapter="fixture:a")
    second = _envelope(b"same", adapter="fixture:b")
    child = _envelope(b"child", parent=first.content_sha256)
    with pytest.raises(SyntheticObservationLineageRejected, match="ambiguous"):
        _review((first, second, child))


def test_cross_source_parent_is_denied():
    root = _envelope(b"root", source="fixture-a")
    child = _envelope(
        b"child", parent=root.content_sha256, source="fixture-b",
    )
    with pytest.raises(SyntheticObservationLineageRejected, match="source boundary"):
        _review((root, child))


def test_parent_must_not_be_timestamped_after_child():
    parent = _envelope(b"parent", at=105)
    child = _envelope(b"child", parent=parent.content_sha256, at=100)
    with pytest.raises(SyntheticObservationLineageRejected, match="after child"):
        _review((parent, child))


def test_same_timestamp_cycle_is_rejected():
    a = _envelope(b"a", parent=_digest(b"b"))
    b = _envelope(b"b", parent=_digest(b"a"))
    with pytest.raises(SyntheticObservationLineageRejected, match="cycle"):
        _review((a, b))


def test_self_parent_cycle_is_rejected():
    root = _envelope(b"root", parent=_digest(b"root"))
    with pytest.raises(SyntheticObservationLineageRejected, match="cycle"):
        _review((root,))


def test_mismatched_privacy_scope_fails_closed():
    root = _envelope(b"root", scope="local:other")
    with pytest.raises(ValueError, match="scope"):
        _review((root,))


def test_cached_media_expiry_is_rejected_at_use_time():
    root = _envelope(b"root")
    assert _review((root,), at=110).checked_at_ms == 110
    with pytest.raises(ValueError, match="age budget"):
        _review((root,), at=111)


def test_clock_rollback_and_invalid_bounds_are_rejected():
    root = _envelope(b"root")
    with pytest.raises(ValueError, match="future"):
        _review((root,), at=99)
    with pytest.raises(ValueError, match="exact"):
        _review((root,), at=True)


def test_bad_tuple_type_is_rejected_before_observation_processing():
    with pytest.raises(SyntheticObservationLineageRejected, match="exact"):
        _review([_envelope(b"root")])


def test_reflected_invalid_digest_is_rejected():
    root = _envelope(b"root")
    object.__setattr__(root, "content_sha256", "invalid")
    with pytest.raises(ValueError, match="content_sha256"):
        _review((root,))


def test_empty_parent_graph_is_rejected():
    with pytest.raises(ValueError, match="nonempty"):
        _review(())
