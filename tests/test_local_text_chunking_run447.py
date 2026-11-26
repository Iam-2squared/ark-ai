"""Isolated synthetic, local-only text chunking and membership tests."""

import hashlib
from dataclasses import replace

import pytest

from ark import local_text_chunking as mod

SHA_A = "a" * 64
SHA_B = "b" * 64


def source(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def request(text: str = "abc🙂日本語", *, budget: int = 6, count: int = 64):
    return mod.LocalChunkRequest(text, source(text), SHA_A, SHA_B, budget, count)


def test_round_trip_without_truncation():
    batch = mod.chunk_local_text(request())
    assert mod.verify_local_chunks(batch) == "abc🙂日本語"
    assert tuple(row.text for row in batch.chunks) == ("abc", "🙂", "日本", "語")
    assert tuple((row.start, row.end) for row in batch.chunks) == (
        (0, 3), (3, 4), (4, 6), (6, 7),
    )
    assert not batch.disclosure_authorized
    assert not batch.source_authenticated
    assert not batch.retention_authorized


def test_unicode_codepoints_never_split_and_deterministic():
    text = "e\u0301🙂\u200b日本" * 10
    a = mod.chunk_local_text(request(text, budget=5))
    b = mod.chunk_local_text(request(text, budget=5))
    assert a == b
    assert mod.verify_local_chunks(a) == text
    assert all(len(row.text.encode("utf-8")) <= 5 for row in a.chunks)


def test_empty_source_denied():
    with pytest.raises(mod.LocalChunkRejected):
        mod.chunk_local_text(mod.LocalChunkRequest("", source(""), SHA_A, SHA_B))


def test_single_codepoint_too_large_denied():
    with pytest.raises(mod.LocalChunkRejected, match="codepoint"):
        mod.chunk_local_text(request("🙂", budget=3))


def test_chunk_limit_never_silently_truncates():
    with pytest.raises(mod.LocalChunkRejected, match="truncate"):
        mod.chunk_local_text(request("abcdefghijk", budget=2, count=2))


def test_exact_limit_and_max_source():
    text = "a" * 65_536
    batch = mod.chunk_local_text(request(text, budget=4_096))
    assert len(batch.chunks) == 16
    assert mod.verify_local_chunks(batch) == text


def test_source_too_big_denied():
    with pytest.raises(mod.LocalChunkRejected, match="byte budget"):
        mod.chunk_local_text(request("a" * 65_537, budget=4_096))


@pytest.mark.parametrize("bad", [0, -1, 4097, 1.0, True, "32", None])
def test_invalid_chunk_byte_budget(bad):
    with pytest.raises(mod.LocalChunkRejected):
        mod.chunk_local_text(replace(request(), chunk_byte_limit=bad))


@pytest.mark.parametrize("bad", [0, -1, 65, 1.0, True, "8", None])
def test_invalid_chunk_count_budget(bad):
    with pytest.raises(mod.LocalChunkRejected):
        mod.chunk_local_text(replace(request(), chunk_limit=bad))


@pytest.mark.parametrize("field", ["source_sha256", "owner_sha256", "scope_sha256"])
def test_wrong_identity_digest_shape(field):
    with pytest.raises(mod.LocalChunkRejected):
        mod.chunk_local_text(replace(request(), **{field: "Z" * 64}))


def test_mismatched_source_digest_denied():
    with pytest.raises(mod.LocalChunkRejected, match="mismatch"):
        mod.chunk_local_text(replace(request(), source_sha256=SHA_A))


def test_bool_and_inherited_request_denied():
    class Surrogate(mod.LocalChunkRequest):
        pass

    with pytest.raises(mod.LocalChunkRejected):
        mod.chunk_local_text(Surrogate("abc", source("abc"), SHA_A, SHA_B))


def test_lone_surrogate_denied():
    with pytest.raises(mod.LocalChunkRejected, match="Unicode"):
        mod.chunk_local_text(mod.LocalChunkRequest("\ud800", SHA_A, SHA_A, SHA_B))


def test_edited_chunk_content_denied():
    batch = mod.chunk_local_text(request())
    bad = replace(batch.chunks[0], text="zzz")
    with pytest.raises(mod.LocalChunkRejected, match="digest"):
        mod.verify_local_chunks(replace(batch, chunks=(bad, *batch.chunks[1:])))


def test_removed_last_chunk_denied():
    batch = mod.chunk_local_text(request())
    with pytest.raises(mod.LocalChunkRejected):
        mod.verify_local_chunks(replace(batch, chunks=batch.chunks[:-1]))


def test_reordered_chunk_denied():
    batch = mod.chunk_local_text(request())
    with pytest.raises(mod.LocalChunkRejected):
        mod.verify_local_chunks(replace(batch, chunks=tuple(reversed(batch.chunks))))


def test_changed_owner_denied_without_bundle_rehash():
    batch = mod.chunk_local_text(request())
    with pytest.raises(mod.LocalChunkRejected, match="membership"):
        mod.verify_local_chunks(replace(batch, owner_sha256=SHA_B))


def test_equal_value_source_replacement_during_hash_denied(monkeypatch):
    subject = request("a" * 128)
    original = hashlib.sha256
    used = False

    def mutating_hash(data=b""):
        nonlocal used
        if not used:
            used = True
            object.__setattr__(subject, "text", ("" + subject.text).encode().decode())
        return original(data)

    monkeypatch.setattr(mod.hashlib, "sha256", mutating_hash)
    # Python may reuse the same string object; use an explicitly distinct carrier.
    if used:
        pytest.fail("mutation was invoked early")
    with pytest.raises(mod.LocalChunkRejected, match="changed"):
        mod.chunk_local_text(subject)


def test_no_disk_or_network_capabilities_exposed():
    batch = mod.chunk_local_text(request("hello"))
    assert not hasattr(batch, "dispatch")
    assert not hasattr(batch, "save")
