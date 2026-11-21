"""Metadata-only local Memory delta: no source trust, deletion proof or replay."""

from dataclasses import FrozenInstanceError

import pytest

from ark.offline_memory_delta import (
    OfflineMemoryDeltaRejected,
    OfflineMemoryRemovalClaim,
    OfflineMemoryRowClaim,
    OfflineMemorySnapshotClaim,
    fingerprint_offline_memory_snapshot,
    review_offline_memory_delta,
)

OWNER = "a" * 64
SCOPE = "b" * 64
CONTENT = "c" * 64
OTHER = "d" * 64
EVENT = "e" * 64
A = "mem_" + "1" * 16
B = "mem_" + "2" * 16


def row(record_id=A, *, content=CONTENT, revision=1, created=100, expires=2000, scope=SCOPE):
    return OfflineMemoryRowClaim(record_id, scope, content, revision, created, expires)


def snap(rows=(), *, now=1000, owner=OWNER):
    return OfflineMemorySnapshotClaim(owner, now, rows)


def removed(record_id=A, *, scope=SCOPE, revision=2, kind="deleted", when=1100, event=EVENT):
    return OfflineMemoryRemovalClaim(record_id, scope, revision, kind, when, event)


def review(prior, current, *, removals=(), prior_hash=None, current_hash=None):
    return review_offline_memory_delta(
        prior,
        current,
        retained_prior_fingerprint=(prior_hash or fingerprint_offline_memory_snapshot(prior)),
        retained_current_fingerprint=(current_hash or fingerprint_offline_memory_snapshot(current)),
        removals=removals,
    )


def test_empty_snapshots_stable_deterministic_and_denied():
    first, second = snap(), snap(now=1100)
    a = review(first, second)
    b = review(first, second)
    assert a == b
    assert len(a.delta_fingerprint) == 64
    assert (a.added_ids, a.updated_ids, a.removed_ids, a.unchanged_count) == ((), (), (), 0)
    assert not a.source_authenticated
    assert not a.deletion_or_erasure_proven
    assert not a.cross_store_atomicity_verified
    assert not a.tool_dispatch_authorized


def test_addition_and_unchanged_and_revision_update():
    before = snap((row(),), now=1100)
    current = snap((row(), row(B)), now=1150)
    result = review(before, current)
    assert result.added_ids == (B,)
    assert result.updated_ids == ()
    assert result.unchanged_count == 1
    revised = snap((row(content=OTHER, revision=2), row(B)), now=1200)
    next_result = review(current, revised)
    assert next_result.updated_ids == (A,)
    assert next_result.unchanged_count == 1
    assert result.delta_fingerprint != next_result.delta_fingerprint
    assert A not in repr(next_result)


def test_explicit_deleted_and_expired_removal_metadata():
    first = snap((row(expires=1170),), now=1100)
    future = snap(now=1250)
    assert review(first, future, removals=(removed(when=1110),)).removed_ids == (A,)
    claim = removed(kind="expired", when=1170)
    assert review(first, future, removals=(claim,)).removed_ids == (A,)


@pytest.mark.parametrize(
    "removals",
    [(), (removed(), removed()), (removed(B),), (removed(revision=3),),
     (removed(scope=OTHER),), (removed(event="broken"),),
     (removed(when=999),), (removed(when=1251),),
     (removed(kind="other"),), (removed(revision=True),),
     (removed(kind="expired", when=1101),)],
)
def test_unauthorized_or_incomplete_removal_rejected(removals):
    with pytest.raises(OfflineMemoryDeltaRejected):
        review(snap((row(expires=1170),), now=1100), snap(now=1250), removals=removals)


@pytest.mark.parametrize(
    "newrow",
    [row(content=OTHER), row(expires=3000), row(revision=0), row(revision=3),
     row(revision=True), row(scope=OTHER, revision=2),
     row(created=101, revision=2), row(revision=2, created=101),
     row(revision=2**63), row(content=OTHER, revision=3)],
)
def test_invalid_revision_or_immutable_identity_rejected(newrow):
    with pytest.raises(OfflineMemoryDeltaRejected):
        review(snap((row(),), now=1100), snap((newrow,), now=1200))


@pytest.mark.parametrize(
    "bad",
    [row(record_id="mem_bad"), row(scope="a"), row(content="x"),
     row(revision=False), row(revision=2**63), row(created=-1),
     row(expires=1000), row(expires=True), row(created=True),
     row(record_id=["unhashable"]), row(content=["invalid"]),
     row(record_id="mem_" + "F" * 16)],
)
def test_invalid_snapshot_row_rejected(bad):
    with pytest.raises(OfflineMemoryDeltaRejected):
        fingerprint_offline_memory_snapshot(snap((bad,)))


def test_sorted_membership_duplicate_and_epoch_limit():
    with pytest.raises(OfflineMemoryDeltaRejected):
        fingerprint_offline_memory_snapshot(snap((row(B), row(A))))
    with pytest.raises(OfflineMemoryDeltaRejected):
        fingerprint_offline_memory_snapshot(snap((row(), row())))
    with pytest.raises(OfflineMemoryDeltaRejected):
        fingerprint_offline_memory_snapshot(snap(tuple(row(f"mem_{i:016x}") for i in range(65))))
    with pytest.raises(OfflineMemoryDeltaRejected):
        fingerprint_offline_memory_snapshot(snap((row(),), now=2**63))
    with pytest.raises(OfflineMemoryDeltaRejected):
        fingerprint_offline_memory_snapshot(snap((row(),), now=True))


def test_new_row_must_start_at_revision_one():
    with pytest.raises(OfflineMemoryDeltaRejected):
        review(snap(), snap((row(revision=2),), now=1200))


def test_strict_retained_snapshot_fingerprints_owner_and_time():
    before = snap((row(),), now=1000)
    after = snap((row(),), now=1100)
    with pytest.raises(OfflineMemoryDeltaRejected):
        review(before, after, prior_hash="e" * 64)
    with pytest.raises(OfflineMemoryDeltaRejected):
        review(before, after, current_hash="e" * 64)
    with pytest.raises(OfflineMemoryDeltaRejected):
        review(before, snap((row(),), owner=OTHER))
    with pytest.raises(OfflineMemoryDeltaRejected):
        review(after, before)
    with pytest.raises(OfflineMemoryDeltaRejected):
        review(before, after, removals=[])


def test_delta_digest_binds_claimed_event_and_elapsed_time():
    before = snap((row(),), now=1000)
    after = snap(now=1200)
    a = review(before, after, removals=(removed(event=EVENT),))
    b = review(before, after, removals=(removed(event=OTHER),))
    c = review(before, snap(now=1250), removals=(removed(event=EVENT),))
    assert len({a.delta_fingerprint, b.delta_fingerprint, c.delta_fingerprint}) == 3


def test_input_claims_are_frozen_but_this_does_not_authenticate_them():
    claim = row()
    with pytest.raises(FrozenInstanceError):
        claim.revision = 5
    assert not review(snap(), snap()).source_authenticated


def test_exact_types_only_even_when_carriers_look_identical():
    class ImpostorRow(OfflineMemoryRowClaim):
        pass

    with pytest.raises(OfflineMemoryDeltaRejected):
        fingerprint_offline_memory_snapshot(snap((ImpostorRow(A, SCOPE, CONTENT, 1, 100, 2000),)))
    with pytest.raises(OfflineMemoryDeltaRejected):
        review(snap(), snap(), removals=(object(),))
    with pytest.raises(OfflineMemoryDeltaRejected):
        fingerprint_offline_memory_snapshot(object())


def test_non_sensitive_repr_and_explicit_non_authority():
    result = review(snap((row(),)), snap((row(content=OTHER, revision=2),), now=1100))
    assert A not in repr(result)
    assert result.updated_ids == (A,)
    assert result.deletion_or_erasure_proven is False
