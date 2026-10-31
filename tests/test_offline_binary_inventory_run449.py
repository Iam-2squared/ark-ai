"""Detached source-complete binary receipt tests, no external I/O."""

import hashlib
from dataclasses import replace

import pytest

from ark.offline_binary_inventory import (
    OfflineBinaryChunk,
    OfflineBinaryRejected,
    OfflineBinaryRequest,
    inventory_offline_binary,
    verify_offline_binary_inventory,
)

OWNER = "a" * 64
PRIVACY = "b" * 64


def request(data=b"ab\x00cd", chunk_bytes=2):
    return OfflineBinaryRequest(OWNER, PRIVACY, hashlib.sha256(data).hexdigest(),
                                data, chunk_bytes)


def verified(receipt, data):
    return verify_offline_binary_inventory(
        receipt, data, retained_inventory_sha256=receipt.inventory_sha256,
        retained_source_sha256=receipt.source_sha256,
    )


def test_entire_source_spans_with_partial_tail():
    data = b"ab\x00cd"
    receipt = inventory_offline_binary(request(data))
    assert [(x.index, x.start_byte, x.end_byte) for x in receipt.chunks] == [
        (0, 0, 2), (1, 2, 4), (2, 4, 5),
    ]
    assert receipt.source_size == 5
    assert verified(receipt, data) is None
    assert not receipt.consent_verified
    assert not receipt.source_authenticated
    assert not receipt.external_disclosure_authorized
    assert not receipt.automatic_replay_authorized
    assert "ab" not in repr(receipt)


def test_exact_multiple_and_single_byte():
    for data, width, count in [(b"abcd", 2, 2), (b"x", 1, 1),
                               (b"\x00" * 1024, 1024, 1)]:
        receipt = inventory_offline_binary(request(data, width))
        assert len(receipt.chunks) == count
        verified(receipt, data)


def test_repeated_stable_and_scope_separated():
    a = inventory_offline_binary(request())
    b = inventory_offline_binary(request())
    c = inventory_offline_binary(replace(request(), privacy_sha256="c" * 64))
    assert a == b
    assert a.inventory_sha256 != c.inventory_sha256


@pytest.mark.parametrize("change", [
    {"owner_sha256": "X" * 64}, {"privacy_sha256": 123},
    {"source_sha256": "0" * 64}, {"source_bytes": b""},
    {"source_bytes": b"x" * (2 * 1024 * 1024 + 1)},
    {"source_bytes": bytearray(b"a")}, {"source_bytes": memoryview(b"a")},
    {"chunk_bytes": False}, {"chunk_bytes": 0}, {"chunk_bytes": 65537},
    {"chunk_bytes": "2"},
])
def test_reject_unbounded_or_fake_request(change):
    with pytest.raises(OfflineBinaryRejected):
        inventory_offline_binary(replace(request(), **change))


def test_reject_chunk_budget_instead_of_dropping_tail():
    with pytest.raises(OfflineBinaryRejected, match="budget"):
        inventory_offline_binary(request(b"x" * 65, 1))


def test_changed_source_and_independent_retained_hashes():
    r = inventory_offline_binary(request())
    with pytest.raises(OfflineBinaryRejected):
        verified(r, b"ab\x00ce")
    with pytest.raises(OfflineBinaryRejected):
        verify_offline_binary_inventory(
            r, b"ab\x00cd", retained_inventory_sha256="c" * 64,
            retained_source_sha256=r.source_sha256,
        )
    with pytest.raises(OfflineBinaryRejected):
        verify_offline_binary_inventory(
            r, b"ab\x00cd", retained_inventory_sha256=r.inventory_sha256,
            retained_source_sha256="c" * 64,
        )


@pytest.mark.parametrize("row", [
    OfflineBinaryChunk(0, 1, 2, "a" * 64),
    OfflineBinaryChunk(2, 0, 2, "a" * 64),
    OfflineBinaryChunk(0, 0, 3, "a" * 64),
    OfflineBinaryChunk(0, 0, 2, "a" * 64),
    OfflineBinaryChunk(True, 0, 2, "a" * 64),
    OfflineBinaryChunk(0, 0, 2, "invalid"),
])
def test_reject_tampered_first_chunk(row):
    r = inventory_offline_binary(request())
    with pytest.raises(OfflineBinaryRejected):
        verified(replace(r, chunks=(row, *r.chunks[1:])), b"ab\x00cd")


def test_reject_dropped_duplicate_and_reordered_rows():
    r = inventory_offline_binary(request())
    for rows in (r.chunks[:-1], (*r.chunks, r.chunks[-1]),
                 tuple(reversed(r.chunks))):
        with pytest.raises(OfflineBinaryRejected):
            verified(replace(r, chunks=rows), b"ab\x00cd")


def test_receipt_tampering_and_input_type():
    r = inventory_offline_binary(request())
    for mutated in (replace(r, source_size=True), replace(r, chunk_bytes=True),
                    replace(r, source_sha256="0" * 64),
                    replace(r, inventory_sha256="0" * 64),
                    replace(r, chunks=list(r.chunks))):
        with pytest.raises(OfflineBinaryRejected):
            verified(mutated, b"ab\x00cd")
    with pytest.raises(OfflineBinaryRejected):
        verify_offline_binary_inventory(
            object(), b"ab\x00cd",
            retained_inventory_sha256=r.inventory_sha256,
            retained_source_sha256=r.source_sha256,
        )
    with pytest.raises(OfflineBinaryRejected):
        verified(r, bytearray(b"ab\x00cd"))


def test_no_implicit_external_origin_proof():
    r = inventory_offline_binary(request(b"\x00" * 4096, 4096))
    assert len(r.chunks) == 1
    assert not r.source_authenticated
    assert not r.external_disclosure_authorized
